# Suomi.fi Open Data DCAT-AP extension

## Validation

Documents can be validated against this specification with a [SHACL](https://www.w3.org/TR/shacl/) processor using these schema files:

- [avoindata_dcat-ap_shacl.ttl](avoindata_dcat-ap_shacl.ttl)
- [FOAF.ttl](FOAF.ttl)

For example, using [pyshacl](https://pypi.org/project/pyshacl):

    pyshacl -s avoindata_dcat-ap_shacl.ttl -e FOAF.ttl --imports -i rdfs catalog.xml

## Vocabularies

Prefix | URI
-------|----
adms | http://www.w3.org/ns/adms#
dcat | http://www.w3.org/ns/dcat#
dcatap | http://data.europa.eu/r5r/
dct | http://purl.org/dc/terms/
foaf | http://xmlns.com/foaf/0.1/
locn | http://www.w3.org/ns/locn#
owl | http://www.w3.org/2002/07/owl#
odrl | http://www.w3.org/ns/odrl/2/
rdfs | http://www.w3.org/2000/01/rdf-schema#
schema | http://schema.org/
skos | http://www.w3.org/2004/02/skos/core#
spdx | http://spdx.org/rdf/terms#
xsd | http://www.w3.org/2001/XMLSchema#
vann | http://purl.org/vocab/vann/
voaf | http://purl.org/vocommons/voaf#
vcard | http://www.w3.org/2006/vcard/ns#
geodcat | http://data.europa.eu/930/#
gsp | http://www.opengis.net/ont/geosparql#


## Classes


### Catalog

#### Catalogue

A catalogue or repository that hosts the Datasets being described.

#### Properties



##### Mandatory
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dcat:dataset | dcat:Dataset | 1..n | This property links the Catalogue with a Dataset that is part of the Catalogue.
dct:description | rdfs:Literal | 1..n | This property contains a free-text account of the Catalogue. This property can be repeated for parallel language versions of the description. For further information on multilingual issues, please refer to section 8.
dct:publisher | foaf:Agent | 1..1 | This property refers to an entity (organisation) responsible for making the Catalogue available.
dct:title | rdfs:Literal | 1..n | This property contains a name given to the Catalogue. This property can be repeated for parallel language versions of the name.
 



##### Recommended
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
foaf:homepage | foaf:Document | 0..1 | This property refers to a web page that acts as the main page for the Catalogue.
dct:language | dct:LinguisticSystem | 0..n | This property refers to a language used in the textual metadata describing titles, descriptions, etc. of the Datasets in the Catalogue. This property can be repeated if the metadata is provided in multiple languages.
dct:issued                                                                                                                                                                                                                       │ | rdfs:Literal typed as xsd:date or xsd:dateTime                                                                                                                                                                                  │ | 0                                                                                                                                                                                                                                 │..1 | This property contains the date of formal issuance (e.g., publication) of the Catalogue.                                                                                                                                  │
dct:spatial | dct:Location | 0..n | This property refers to a geographical area covered by the Catalogue.
dct:modified | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the most recent date on which the Catalogue was modified.
 



##### Optional
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dct:rights | dct:RightsStatement | 0..1 | This property refers to a statement that specifies rights associated with the Catalogue.
dcat:dataservice | dcat:DataService | 0..n | This property refers to a site or end-point that is listed in the catalog.
 

 

### Dataset

#### Dataset

A conceptual entity that represents the information published.

#### Properties



##### Mandatory
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dct:description | rdfs:Literal | 1..n | This property contains a free-text account of the Dataset. This property can be repeated for parallel language versions of the description.
dct:title | rdfs:Literal | 1..n | This property contains a name given to the Dataset. This property can be repeated for parallel language versions of the name.
 



##### Recommended
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dcat:contactPoint | vcard:Kind | 0..n | This property contains contact information that can be used for sending comments about the Dataset.
dcat:distribution | dcat:Distribution | 0..n | This property links the Dataset to an available Distribution.
dcat:keyword | rdfs:Literal | 0..n | This property contains a keyword or tag describing the Dataset.
dct:publisher | foaf:Agent | 0..1 | This property refers to an entity (organisation) responsible for making the Dataset available.
dct:spatial | dct:Location | 0..n | This property refers to a geographic region that is covered by the Dataset.
dct:temporal | dct:PeriodOfTime | 0..1 | This property refers to a temporal period that the Dataset covers.
dcat:theme, subproperty of dct:subject | skos:Concept | 0..n | This property refers to a category of the Dataset. A Dataset may be associated with multiple themes.
 



##### Optional
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dct:accessRights | dct:RightsStatement | 0..1 | This property refers to information that indicates whether the Dataset is open data, has access restrictions or is not public. A controlled vocabulary with three members (:public, :restricted, :non-public) will be created and maintained by the Publications Office of the EU.
dct:creator | foaf:Agent | 0..1 | This property refers to the  entity primarily responsible for producing the dataset
dct:accrualPeriodicity | dct:Frequency | 0..1 | This property refers to the frequency at which the Dataset is updated.
dct:identifier | rdfs:Literal | 0..n | This property contains the main identifier for the Dataset, e.g. the URI or other unique identifier in the context of the Catalogue.
dcat:landingPage | foaf:Document | 0..n | This property refers to a web page that provides access to the Dataset, its Distributions and/or additional information. It is intended to point to a landing page at the original data provider, not to a page on a site of a third party, such as an aggregator.
dct:issued | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the date of formal issuance (e.g., publication) of the Dataset.
dcat:spatialResolutionInMeters | xsd:decimal | 0..n | This property refers to the minimum spatial separation resolvable in a dataset, measured in meters.
dcat:temporalResolution | xsd:duration | 0..n | This property refers to the minimum time period resolvable in the dataset.
dct:type | skos:Concept | 0..1 | This property refers to the type of the Dataset. A controlled vocabulary for the values has not been established.
dct:modified | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the most recent date on which the Dataset was changed or modified.
geodcat:custodian | foaf:Agent | 0..n | Party that accepts accountability and responsibility for the data and ensures appropriate care and maintenance of the resource [ISO-19115].
 

 

### Distribution

#### Distribution

A physical embodiment of the Dataset in a particular format.

#### Properties



##### Mandatory
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dcat:accessURL | rdfs:Resource | 1..n | This property contains a URL that gives access to a Distribution of the Dataset. The resource at the access URL may contain information about how to get the Dataset.
 



##### Recommended
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dct:description | rdfs:Literal | 0..n | This property contains a free-text account of the Distribution. This property can be repeated for parallel language versions of the description.
dct:format | dct:MediaTypeOrExtent | 0..1 | This property refers to the file format of the Distribution.
dct:license | dct:LicenseDocument | 0..1 | This property refers to the licence under which the Distribution is made available.
 



##### Optional
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dcat:byteSize | rdfs:Literal typed as xsd:decimal | 0..1 | This property contains the size of a Distribution in bytes.
spdx:checksum | spdx:Checksum | 0..1 | This property provides a mechanism that can be used to verify that the contents of a distribution have not changed. The checksum is related to the downloadURL.
dcat:downloadURL | rdfs:Resource | 0..n | This property contains a URL that is a direct link to a downloadable file in a given format.
dcat:mediaType, subproperty of dct:format | dct:MediaType | 0..1 | This property refers to the media type of the Distribution as defined in the official register of media types managed by IANA.
dct:issued | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the date of formal issuance (e.g., publication) of the Distribution.
dct:rights | dct:RightsStatement | 0..1 | This property refers to a statement that specifies rights associated with the Distribution.
dcat:spatialResolutionInMeters | xsd:decimal | 0..n | This property refers to the  minimum spatial separation resolvable in a dataset distribution, measured in meters.
adms:status | skos:Concept | 0..1 | This property refers to the maturity of the Distribution. It MUST take one of the values Completed, Deprecated, Under Development, Withdrawn.
dcat:temporalResolution | xsd:duration | 0..n | This property refers to the minimum time period resolvable in the dataset distribution.
**dct:temporal** | dct:PeriodOfTime | 0..n | This property refers to a temporal period that the Distribution covers.
dct:title | rdfs:Literal | 0..n | This property contains a name given to the Distribution. This property can be repeated for parallel language versions of the description.
dct:modified | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the most recent date on which the Distribution was changed or modified.
dcat:spatialResolutionInMeters | rdfs:Literal typed as xsd:decimal | 0..1 | This property tells the accuracy of geospatial data in meters
 

 

### DataService

#### Data Service

A collection of operations that provides access to one or more datasets or data processing functions.

#### Properties



##### Mandatory
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dcat:endpointURL | rdfs:Resource | 1..n | The root location or primary endpoint of the service (an IRI).
dct:title | rdfs:Literal | 1..n | This property contains a name given to the Data Service. This property can be repeated for parallel language versions of the name.
 



##### Recommended
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dcat:endpointDescription | rdfs:Resource | 0..n | This property contains a  description of the services available via the end-points, including their operations, parameters etc.The property gives specific details of the actual endpoint instances, while dct:conformsTo is used to indicate the general standard or specification that the endpoints implement.
 



##### Optional
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dct:accessRights | dct:RightsStatement | 0..1 | This property MAY include information regarding access or restrictions based on privacy, security, or other policies.
dct:description | rdfs:Literal | 0..n | This property contains a free-text account of the Data Service. This property can be repeated for parallel language versions of the description.
dct:license | dct:LicenseDocument | 0..1 | This property contains  the licence under which the Data service is made available.
 

 

### Showcase


  Sub-class of dcat:Resource
#### Showcase

A conceptual entity that represents the information about showcase.

#### Properties



##### Mandatory
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dcat:description | rdfs:Resource | 1..n | This property contains a free-text account of the Showcase. This property can be repeated for parallel language versions of the description.
dct:title | rdfs:Literal | 1..n | This property contains a name given to the Showcase. This property can be repeated for parallel language versions of the name.
adfi:dataUserInterface | rdfs:Literal | 1..1 | The showcase’s URL on Suomi.fi Open Data. The URL is created automatically based on the publisher’s name. You can edit the URL if you want.
 



##### Recommended
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dcat:theme, subproperty of dct:subject | skos:Concept | 0..n | This property refers to a category of the Showcase. A Showcase may be associated with multiple themes.
adfi:platform | rdfs:Literal | 0..n | If you have created a mobile or desktop showcase, select which platforms it supports.
dcat:keyword | rdfs:Literal | 0..n | Keywords help users to find your showcase. Select at least one keyword in Finnish.
dct:creator | foaf:name | 1..1 | Developer of showcase
adfi:creatorWebsiteUri | rdfs:Literal | 0..1 | Website of developer
dcat:landingPage | rdfs:Literal | 0..1 | Website of showcase
adfi:distributor | rdfs:Literal | 0..n | Distributor urls
dct:description | rdfs:Literal | 1..n | A short and descriptive explanation about the showcase. Tell for example about possible applications and the creation process, as well as about how open data has been used in the showcase.
adfi:applicationIcon | rdfs:Literal | 0..1 | A short and descriptive explanation about the showcase. Tell for example about possible applications and the creation process, as well as about how open data has been used in the showcase.
adfi:previewMedia | rdfs:Literal | 0..3 | Add max. 3 images of your showcase. Good images are for example those that show the user interface and features of the showcase.
adfi:archived | rdfs:Literal | 0..1 | Tells if showcase is archived
 



 
 
