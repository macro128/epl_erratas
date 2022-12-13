# epl_erratas

An app for generating [ePubLibre](https://www.epublibre.org/) errata reports.

## Supported vendors

Right now only devices made from the following vendors can be used to generate reports:

* Kindle

## Deploy

To deploy this app docker compose is needed, use the following command to start it:

```bash
bash deploy/docker-compose.sh up
```

## Development

For development a docker compose environment is created and source contents are shared with the container, use the following command to start the container:

```bash
bash deploy/docker-compose.sh -d up
```
