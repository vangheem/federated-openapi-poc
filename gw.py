import asyncio
import os
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import pydantic
from fastapi import FastAPI
from starlette.responses import JSONResponse


class Downstream(pydantic.BaseModel):
    base_url: str
    openapi_url: str
    spec: Optional[Dict[str, Any]] = None


DOWNSTREAMS = [
    Downstream(
        openapi_url="http://localhost:8880/openapi.json",
        base_url="http://localhost:8880",
    ),
    Downstream(
        openapi_url="http://localhost:8881/openapi.json",
        base_url="http://localhost:8881",
    ),
    Downstream(
        openapi_url="http://localhost:8882/openapi.json",
        base_url="http://localhost:8882",
    ),
]


def get_json_schema_dm(downstream, ref):
    parts = ref.replace("#/", "").split("/")
    loc = downstream.spec
    for part in parts:
        try:
            loc = loc[part]
        except KeyError:
            return None
    return loc


def find_resolver_paths(result, ref):
    results = []
    for downstream in DOWNSTREAMS:
        for path, path_data in downstream.spec["paths"].items():
            if "get" not in path_data.keys():
                continue
            aref = path_data["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["$ref"]
            if aref != ref:
                continue
            model = get_json_schema_dm(downstream, ref)
            if model is None:
                continue

            # check if we have to fill data this endpoint provides
            if len(set(model["properties"].keys()) - set(result.keys())) > 0:
                real_path = []
                for path_part in path.split("/"):
                    if len(path_part) > 1 and path_part[0] == "{":
                        # need to replace variable with part of data
                        path_part = result[path_part.strip("{}")]
                    real_path.append(path_part)
                results.append(("/".join(real_path), downstream))
    return results


class GatewayApp(FastAPI):
    specs = []
    session: aiohttp.ClientSession

    def __init__(self):
        super().__init__(on_startup=[self.startup])

    async def startup(self) -> None:
        # load downstreams
        self.session = aiohttp.ClientSession()
        for downstream in DOWNSTREAMS:
            async with self.session.get(downstream.openapi_url) as resp:
                downstream.spec = await resp.json()

    async def result_merger(
        self,
        matches: List[Tuple[str, Downstream]],
        result: Dict[str, Any],
        ref: str,
    ):
        for path, downstream in matches:
            url = os.path.join(downstream.base_url, path.lstrip("/"))
            async with self.session.get(url) as resp:
                result.update(await resp.json())

        # look for referenced refs to check resolution for
        for downstream in DOWNSTREAMS:
            model = get_json_schema_dm(downstream, ref)
            if model is None:
                continue

            for name, prop in model["properties"].items():
                if name not in result:
                    continue

                if prop.get("type") == "array" and "$ref" in prop["items"]:
                    reqs = []
                    sub_ref = prop["items"]["$ref"]
                    for sub_result in result[name]:
                        reqs.append(
                            self.result_merger(
                                find_resolver_paths(sub_result, sub_ref),
                                sub_result,
                                sub_ref,
                            )
                        )
                    await asyncio.wait(reqs)

                if "$ref" in prop:
                    await self.result_merger(
                        find_resolver_paths(result[name], prop["$ref"]),
                        result[name],
                        prop["$ref"],
                    )

    async def __call__(self, scope, receive, send) -> None:
        scope["app"] = self

        assert scope["type"] in ("http", "websocket", "lifespan")

        if scope["type"] == "lifespan":
            await self.router.lifespan(scope, receive, send)
            return

        # match incoming url
        matches = []
        ref = None
        path_parts = scope["path"].split("/")

        for downstream in DOWNSTREAMS:
            for path, path_data in downstream.spec["paths"].items():
                if "get" not in path_data.keys():
                    continue

                if len(path_parts) != len(path.split("/")):
                    continue

                for idx, path_part in enumerate(path.split("/")):
                    if idx >= len(path_parts):
                        break
                    if path_parts[idx] != path_part:
                        if path_part[0] == "{":
                            continue
                        else:
                            break
                else:
                    ref = path_data["get"]["responses"]["200"]["content"][
                        "application/json"
                    ]["schema"]["$ref"]
                    matches.append((scope["path"], downstream))

        if len(matches) == 0:
            await self.default(scope, receive, send)
        else:
            result = {}
            await self.result_merger(matches, result, ref)
            response = JSONResponse(result, status_code=200)
            await response(scope, receive, send)


app = GatewayApp()
