# Avoindata.fi DCAT-AP extension

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
dct:license | dct:LicenseDocument | 0..1 | This property refers to the licence under which the Catalogue can be used or reused.
dct:issued | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the date of formal issuance (e.g., publication) of the Catalogue.
dct:spatial | dct:Location | 0..n | This property refers to a geographical area covered by the Catalogue.
dcat:themeTaxonomy | skos:ConceptScheme | 0..n | This property refers to a knowledge organization system used to classify the Catalogue's Datasets.
dct:modified | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the most recent date on which the Catalogue was modified.
 

##### Optional
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dct:hasPart | dcat:Catalog | 0..n | This property refers to a related Catalogue that is part of the described Catalogue
dct:isPartOf | dcat:Catalog | 0..1 | This property refers to a related Catalogue in which the described Catalogue is physically or logically included.
dcat:record | dcat:CatalogRecord | 0..n | This property refers to a Catalogue Record that is part of the Catalogue
dct:rights | dct:RightsStatement | 0..1 | This property refers to a statement that specifies rights associated with the Catalogue.
dcat:service | dcat:DataService | 0..n | This property refers to a site or end-point that is listed in the catalog.
dcat:catalog | dcat:Catalog | 0..n | This property refers to a catalog whose contents are of interest in the context of this catalog
dct:creator | foaf:Agent | 0..1 | This property refers to the  entity primarily responsible for producing the catalogue
 
 

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
dct:conformsTo | dct:Standard | 0..n | This property refers to an implementing rule or other specification.
foaf:page | foaf:Document | 0..n | This property refers to a page or document about this Dataset.
dct:accrualPeriodicity | dct:Frequency | 0..1 | This property refers to the frequency at which the Dataset is updated.
dct:hasVersion | dcat:Dataset | 0..n | This property refers to a related Dataset that is a version, edition, or adaptation of the described Dataset.
dct:identifier | rdfs:Literal | 0..n | This property contains the main identifier for the Dataset, e.g. the URI or other unique identifier in the context of the Catalogue.
dct:isReferencedBy | rdfs:Resource | 0..n | This property provides a link to a description of a relationship with another resource
dct:isVersionOf | dcat:Dataset | 0..n | This property refers to a related Dataset of which the described Dataset is a version, edition, or adaptation.
dcat:landingPage | foaf:Document | 0..n | This property refers to a web page that provides access to the Dataset, its Distributions and/or additional information. It is intended to point to a landing page at the original data provider, not to a page on a site of a third party, such as an aggregator.
dct:language | dct:LinguisticSystem | 0..n | This property refers to a language of the Dataset. This property can be repeated if there are multiple languages in the Dataset.
adms:identifier | adms:Identifier | 0..n | This property refers to a secondary identifier of the Dataset, such as MAST/ADS1, DataCite2, DOI3, EZID4 or W3ID5.
dct:provenance | dct:ProvenanceStatement | 0..n | This property contains a statement about the lineage of a Dataset.
prov:qualifiedAttribution | prov:Attribution | 0..n | This property refers to a liink to an Agent having some form of responsibility for the resource
dcat:qualifiedRelation | dcat:Relationship | 0..n | This property is about a  related resource, such as a publication, that references, cites, or otherwise points to the dataset.
dct:relation | rdfs:Resource | 0..n | This property refers to a related resource.
dct:issued | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the date of formal issuance (e.g., publication) of the Dataset.
adms:sample | dcat:Distribution | 0..n | This property refers to a sample distribution of the dataset
dct:source | dcat:Dataset | 0..n | This property refers to a related Dataset from which the described Dataset is derived.
dcat:spatialResolutionInMeters | xsd:decimal | 0..n | This property refers to the minimum spatial separation resolvable in a dataset, measured in meters.
dcat:temporalResolution | xsd:duration | 0..n | This property refers to the minimum time period resolvable in the dataset.
dct:type | skos:Concept | 0..1 | This property refers to the type of the Dataset. A controlled vocabulary for the values has not been established.
dct:modified | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the most recent date on which the Dataset was changed or modified.
owl:versionInfo | rdfs:Literal | 0..1 | This property contains a version number or other version designation of the Dataset.
adms:versionNotes | rdfs:Literal | 0..n | This property contains a description of the differences between this version and a previous version of the Dataset. This property can be repeated for parallel language versions of the version notes.
prov:wasGeneratedBy | prov:Activity | 0..n | This property refers to an activity that generated, or provides the business context for, the creation of the dataset.
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
dcatap:availability | skos:Concept | 0..1 | This property indicates how long it is planned to keep the Distribution of the Dataset available.
dct:description | rdfs:Literal | 0..n | This property contains a free-text account of the Distribution. This property can be repeated for parallel language versions of the description.
dct:format | dct:MediaTypeOrExtent | 0..1 | This property refers to the file format of the Distribution.
dct:license | dct:LicenseDocument | 0..1 | This property refers to the licence under which the Distribution is made available.
 

##### Optional
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dcat:accessService | dcat:DataService | 0..n | This property refers to a data service that gives access to the distribution of the dataset
dcat:byteSize | rdfs:Literal typed as xsd:decimal | 0..1 | This property contains the size of a Distribution in bytes.
spdx:checksum | spdx:Checksum | 0..1 | This property provides a mechanism that can be used to verify that the contents of a distribution have not changed. The checksum is related to the downloadURL.
dcat:compressFormat | dct:MediaType | 0..1 | This property refers to the format of the file in which the data is contained in a compressed form, e.g. to reduce the size of the downloadable file. It SHOULD be expressed using a media type as defined in the official register of media types managed by IANA.
foaf:page | foaf:Document | 0..n | This property refers to a page or document about this Distribution.
dcat:downloadURL | rdfs:Resource | 0..n | This property contains a URL that is a direct link to a downloadable file in a given format.
odrl:hasPolicy | odrl:Policy | 0..1 | This property refers to the policy expressing the rights associated with the distribution if using the ODRL vocabulary
dct:language | dct:LinguisticSystem | 0..n | This property refers to a language used in the Distribution. This property can be repeated if the metadata is provided in multiple languages.
dct:conformsTo | dct:Standard | 0..n | This property refers to an established schema to which the described Distribution conforms.
dcat:mediaType, subproperty of dct:format | dct:MediaType | 0..1 | This property refers to the media type of the Distribution as defined in the official register of media types managed by IANA.
dcat:packageFormat | dct:MediaType | 0..1 | This property refers to the format of the file in which one or more data files are grouped together, e.g. to enable a set of related files to be downloaded together. It SHOULD be expressed using a media type as defined in the official register of media types managed by IANA.
dct:issued | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the date of formal issuance (e.g., publication) of the Distribution.
dct:rights | dct:RightsStatement | 0..1 | This property refers to a statement that specifies rights associated with the Distribution.
dcat:spatialResolutionInMeters | xsd:decimal | 0..n | This property refers to the  minimum spatial separation resolvable in a dataset distribution, measured in meters.
adms:status | skos:Concept | 0..1 | This property refers to the maturity of the Distribution. It MUST take one of the values Completed, Deprecated, Under Development, Withdrawn.
dcat:temporalResolution | xsd:duration | 0..n | This property refers to the minimum time period resolvable in the dataset distribution.
**dct:temporal** | dct:PeriodOfTime | 0..n | This property refers to a temporal period that the Distribution covers.
dct:title | rdfs:Literal | 0..n | This property contains a name given to the Distribution. This property can be repeated for parallel language versions of the description.
dct:modified | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the most recent date on which the Distribution was changed or modified.
dcat:spatialResolutionInMeters | rdfs:Literal typed as xsd:decimal | 0..1 | This property tells the accuracy of geospatial data in meters
 
 

### CatalogueRecord

#### Catalogue Record

A description of a Dataset’s entry in the Catalogue.

#### Properties


##### Mandatory
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
foaf:primaryTopic | dcat:Dataset or dcat:Dataservice or dcat:Catalog | 1..1 | This property links the Catalogue Record to the Dataset, Data service or Catalog described in the record.
dct:modified | rdfs:Literal typed as xsd:date or xsd:dateTime | 1..1 | This property contains the most recent date on which the Catalogue entry was changed or modified.
 

##### Recommended
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dct:conformsTo | dct:Standard | 0..1 | This property refers to an Application Profile that the Dataset’s metadata conforms to
adms:status | skos:Concept | 0..1 | This property refers to the type of the latest revision of a Dataset's entry in the Catalogue.
dct:issued | rdfs:Literal typed as xsd:date or xsd:dateTime | 0..1 | This property contains the date on which the description of the Dataset was included in the Catalogue.
 

##### Optional
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dct:description | rdfs:Literal | 0..n | This property contains a free-text account of the record. This property can be repeated for parallel language versions of the description.
dct:language | dct:LinguisticSystem | 0..n | This property refers to a language used in the textual metadata describing titles, descriptions, etc. of the Dataset. This property can be repeated if the metadata is provided in multiple languages.
dct:source | dcat:CatalogRecord | 0..1 | This property refers to the original metadata that was used in creating metadata for the Dataset
dct:title | rdfs:Literal | 0..n | This property contains a name given to the Catalogue Record. This property can be repeated for parallel language versions of the name.
 
 

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
dcat:servesDataset | dcat:Dataset | 0..n | This property refers to a collection of data that this data service can distribute.
 

##### Optional
Term | Range | Cardinality | Comment
-----|-------|-------------|--------
dct:accessRights | dct:RightsStatement | 0..1 | This property MAY include information regarding access or restrictions based on privacy, security, or other policies.
dct:description | rdfs:Literal | 0..n | This property contains a free-text account of the Data Service. This property can be repeated for parallel language versions of the description.
dct:license | dct:LicenseDocument | 0..1 | This property contains  the licence under which the Data service is made available.
 
 
 
