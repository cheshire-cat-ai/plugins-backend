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


## Caching system

Actually the cache is memory based (reset on shutdown) and it's invalidated once per day (after 1440 minutes)
