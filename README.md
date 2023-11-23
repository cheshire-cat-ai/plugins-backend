# Awesome plugins backend
The backend of The Cheshire Cat plugin directory

## Getting started...

### Using Docker

```bash
$ docker compose up
```

### Using local python environment

Install requirements:   

```bash
$ pip install -r requirements.txt
```

Start uvicorn server:   

```bash
$ python ./main.py
```


## API Documentation

Welcome to the API documentation for our plugin directory. Below, you'll find a list of available endpoints to interact with the system.

### Index

- [List all Plugins (Paginated)](#list-all-plugins-paginated)
- [List Excluded Plugins (Paginated)](#list-excluded-plugins-paginated)
- [List Plugins by Author (Paginated)](#list-plugins-by-author-paginated)
- [Get All Available Tags](#get-all-available-tags)
- [Get Plugins by Tag (Paginated)](#get-plugins-by-tag-paginated)
- [Download a Single Plugin (.zip)](#download-a-single-plugin-zip)
- [Search for a Plugin](#search-for-a-plugin)
- [Get Plugins Analytics](#get-plugins-analytics)


---

### List all Plugins (Paginated)

**GET** `/plugins`

List all the plugins.

**Order Parameter:**

- `order`: Sort plugins list
  - `oldest`: Sort from oldest to newest **(default)**
  - `newest`: Sort from newest to older
  - `popular`: Sort from most popular
  - `a2z`: Sort alphabetically
  - `z2a`: Sort reverse alphabetically

**Pagination Parameters:**

- `page`: Query the page number.
- `page_size`: Query the number of elements per page.

Example: Return the second page, 3 plugins per page ordered from newest to oldest

```plaintext
/plugins?page=2&page_size=3&order=newest
```

---

### List Excluded Plugins (Paginated)

**POST** `/excluded`

List the plugins excluding the ones you pass in the body.

**Request Body:**

```json
{
  "excluded": ["plugin to exclude", "other plugin I don't want"]
}
```

**Pagination Parameters:**

- `page`: Query the page number.
- `page_size`: Query the number of elements per page.

Example: Return the second page, 3 plugins per page

```plaintext
/exclude?page=2&page_size=3
```

---

### List Plugins by Author (Paginated)

**POST** `/author`

List all the plugins from a specific author.

**Request Body:**

```json
{
  "author_name": "Nicola Corbellini"
}
```

**Pagination Parameters:**

- `page`: Query the page number.
- `page_size`: Query the number of elements per page.

Example: Return the second page, 3 plugins per page

```plaintext
/author?page=2&page_size=3
```

---

### Get All Available Tags

**GET** `/tags`

Return the list of all available plugins' tags.

---

### Get Plugins by Tag (Paginated)

**GET** `/tag/{tag}`

Return all the plugins that have a specific tag.

**Pagination Parameters:**

- `page`: Query the page number.
- `page_size`: Query the number of elements per page.

Example: Return the second page, 3 plugins per page

```plaintext
/tag/{tag}?page=2&page_size=3
```

---

### Download a Single Plugin (.zip)

**POST** `/download`

Download a single plugin in `.zip` format.

**Request Body:**

```json
{
  "url": "https://github.com/pieroit/meow-todo-list"
}
```

---

### Search for a Plugin

**POST** `/search`

Search for a plugin. This will perform a search in plugins' description, name, author, and tags.

**Request Body:**

```json
{
  "query": "llm embedding nicola corbellini"
}
```

---  

### Get Plugins' Analytics

**GET** `/analytics`

Return all the plugins' analytics.

![Graph example](https://github.com/cheshire-cat-ai/plugins-backend/assets/3589467/2339f505-d97c-4cd9-816c-37b9b0a42f20)


---  

### Plot Plugins' Analytics Graph

**GET** `/analytics/graph`

Return an HTML webpage with an image of plugins' analytics graph.

---  

## Plugin manifest validation

The validation process for the plugin.json manifest ensures the integrity and usability of plugins within the repository. 
To successfully pass validation, the plugin.json file must reside within the main branch of the repository and include essential fields such as "name" and "author_name". 
While other fields remain optional, including additional information not only enhances the user experience but also improves searchability within the directory. 
Maintaining these validation criteria not only guarantees the quality of plugins but also contributes to a more robust and user-friendly plugin ecosystem.

## Caching System

Our caching system is designed to optimize performance and reduce redundant operations. 
Currently, most of the caching is memory-based, which means it gets reset upon system shutdown. 
Additionally, our cache is **invalidated on a daily basis**, precisely every 1440 minutes.

### File Cache

When the `/download` endpoint is initially called, our system sets up two essential folders: `zip_cache` and `repository_cache`.

- `zip_cache` stores the release zip files or acts as a creation location if there are no existing releases on GitHub.
- `repository_cache` is used to clone repositories that lack releases.

We employ a comprehensive strategy to determine whether a repository or release has been downloaded and whether it's up-to-date. 
If the repository is present and current, we retrieve and provide the existing zip file. 
However, if the repository is outdated or if any issues arise while verifying its status, the existing repository is deleted. 
Subsequently, we initiate a fresh download to ensure accuracy.

This approach serves two key purposes: efficient repository caching and the prevention of unnecessary cloning operations when a repository is already available and up-to-date.

## Analytics

The implementation of analytics within our plugin's directory is designed with utmost consideration for user privacy.
We maintain an `analytics.json` file that is updated each time a plugin is downloaded, providing us with valuable insights into usage trends without compromising individual user identities.
Importantly, we do not track unique downloads or store any sensitive data such as IP addresses.
Our approach to analytics prioritizes user privacy, ensuring that our data collection methods, while not overly precise, remain fair and respectful of the privacy of our users.
This commitment to data ethics underscores our dedication to creating a transparent and user-friendly environment within our plugin ecosystem.
