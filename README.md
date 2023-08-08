# Awesome plugins backend
The backend of The Cheshire Cat plugin directory

## Getting started

Install requirements:   

```bash
$ pip install -r requirements.txt
```

Start uvicorn server:   

```bash
$ python ./main.py
```


## Endpoint list

**GET**   

```
/plugins
```

List all the plugins (paginated)

**Pagination Parameters**

`page`: query the page number   

`page_size`: query the number of elements per page

Eg. return the second page, 3 plugins per page 
```
/plugins?page=1&page_size=3
```   

---   

**POST**   

```
/excluded
```

List the plugins excluding the ones you pass in the body (paginated)

**Request Body:**   

```json
{
  "excluded": ["plugin to exclude", "other plugin I don't want"]
}
```
**Pagination Parameters**

`page`: query the page number   

`page_size`: query the number of elements per page

Eg. return the second page, 3 plugins per page 
```
/exclude?page=1&page_size=3
```   

---   


**POST**   

```
/author
```

List all the plugins from a specific author (paginated)

**Request Body:**   

```json
{
  "author_name": "Nicola Corbellini"
}
```
**Pagination Parameters**

`page`: query the page number   

`page_size`: query the number of elements per page

Eg. return the second page, 3 plugins per page 
```
/author?page=1&page_size=3
```   

---   

**GET**   

```
/tags
```

Returns the list of all available plugins' tags   

---   

**GET**   

```
/tag/{tag}
```

Returns all the plugin that has a specific tag   

**Pagination Parameters**

`page`: query the page number   

`page_size`: query the number of elements per page

Eg. return the second page, 3 plugins per page 
```
/tag/{tag}?page=1&page_size=3
```   

---   


**POST**   

```
/download
```

Download a single plugin (.zip)

**Request Body:**   

```json
{
  "plugin_name": "mood music"
}
```

---   


## Caching system

Actually almost all the cache is memory based (reset on shutdown) and it's invalidated once per day (after 1440 minutes)

### File cache

The first time `/download` is called two folders will be created: `zip_cache` and `repository_cache`

- `zip_cache` is the folder where the zip files are stored while they are created   
- `repository_cache` is the folder where we clone repositories

We check whether the repository is already cloned and whether it's up-to-date. If the repository exists and is up-to-date, we return the existing repository path.
If it's not up-to-date or if there's an error while checking the repository status, the existing repository is deleted, and a fresh clone is performed.

This approach allows us to cache repositories and avoid unnecessary cloning when the repository is already available and up-to-date.
If the repository has changed or there's an error, the cache is invalidated, and a new clone is performed.