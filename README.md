# Awesome plugins backend
The backend of The Cheshire Cat plugin directory

## Getting started

Install requirements:   

```bash
$ pip install -r requirements.txt
```

Start uvicorn server:   

```bash
$ uvicorn main:app --reload
```


## Endpoint list

```
/plugins
```

List all the plugins (paginated)

**Pagination Parameters**

`page`: query the page number   

`page_size`: query the number of elements per page

Eg. return the second page, 3 plugins per page 
```
/plugins?page=1&page_size=2
```   

---   


```
/tags
```

Returns the list of all available plugins' tags   

---   


```
/tag/{tag}
```

Returns all the plugin that has a specific tag   

**Pagination Parameters**

`page`: query the page number   

`page_size`: query the number of elements per page

Eg. return the second page, 3 plugins per page 
```
/tag/{tag}?page=1&page_size=2
```   


---   


## Caching system

Actually the cache is memory based (reset on shutdown) and it's invalidated once per day (after 1440 minutes)
