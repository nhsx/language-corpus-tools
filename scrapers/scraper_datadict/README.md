This scraper retrieves the NHS Data Dictionary (https://datadictionary.nhs.uk/) and stores it in a local database.

The database consists of two tables: dictionary_item and link. The former contains a dictionary item of any type (class, attribute, element, business
definition or dataset) and the latter represents a link between two dictionary items.

It was designed to be as generic as possible, while still allow to re-create the same representation and functionality as the original web site. Any
cross-references found in the description are converted into a specially formatted html link, e.g.:

```html
<a data-item-type="class" data-item-id="accommodation">ACCOMMODATION</a>
```

The data model theoretically allows ingestion of other dictionaries.

The detailed database structure can be found in appstack/services/db_init/scripts/datadict.sql
