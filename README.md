# POC Federated OpenAPI Gateway

The purpose of this repository is to provide a POC federated GraphQL implementation.

The initial idea is briefly [in my blog post](https://www.nathanvangheem.com/posts/2021/04/19/federated-rest-api-gw.html).

To run this POC, you will need Python + Poetry. Then:

```
poetry install
```

Then, run each of the services:

```
poetry run uvicorn users:app --reload --port=8880
poetry run uvicorn products:app --reload --port=8881
poetry run uvicorn reviews:app --reload --port=8882
poetry run uvicorn gw:app --reload --port=8888
```

Then, you can make requests to `localhost:8888/users` or `localhost:8888/users/2` to see how
the Federated OpenAPI Gateway works in composing the services together.
