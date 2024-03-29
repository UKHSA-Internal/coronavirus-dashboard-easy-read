# Coronavirus (COVID-19) in the UK - Easy-Read

![GitHub commit activity](https://img.shields.io/github/commit-activity/y/publichealthengland/coronavirus-dashboard-easy-read)
[![Language grade: JavaScript](https://img.shields.io/lgtm/grade/javascript/g/publichealthengland/coronavirus-dashboard-easy-read.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/publichealthengland/coronavirus-dashboard-easy-read/context:javascript)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/publichealthengland/coronavirus-dashboard-easy-read.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/publichealthengland/coronavirus-dashboard-easy-read/context:python)

This is the source code for the [easy read pages](https://coronavirus.data.gov.uk/easy_read) and PDF generator.

## Other repositories

Different parts of the Coronavirus dashboard service are maintained in their respective 
repositories, itemised as follows:
 
- [API v.1](https://github.com/publichealthengland/coronavirus-dashboard-api-v1) - Main API service for the data, lookup tables, CMS, and metadata.
- [API v.2.0](https://github.com/publichealthengland/coronavirus-dashboard-api-v2) - Batch downloads service [DEPRECATED in favour of v2.1]
- [API v.2.1](https://github.com/publichealthengland/coronavirus-dashboard-api-v2-server) - Batch downloads service
- [Generic APIs](https://github.com/publichealthengland/coronavirus-dashboard-generic-apis) - APIs that power the map, navigation, hierarchy, and relations
- [Coronavirus Dashboard](https://github.com/publichealthengland/coronavirus-dashboard) - Details pages
- [Frontend Server](https://github.com/publichealthengland/coronavirus-dashboard-frontend-server) - Home and Postcode pages
- [Layout CMS](https://github.com/publichealthengland/coronavirus-dashboard-layouts) - Definition of contents
- [Metadata](https://github.com/publichealthengland/coronavirus-dashboard-metadata) - Description of metrics and textual contents
- [ETL Service](https://github.com/publichealthengland/coronavirus-dashboard-pipeline-etl) - Post-pipeline data processing and deployment
- [Terraform](https://github.com/publichealthengland/coronavirus-dashboard-terraform) - Infrastructure as Code [DEPRECATED in favour of ARM templates]


## Development and contribution

We welcome contributions by everyone. Please read 
the [contributions guide](https://github.com/PublicHealthEngland/coronavirus-dashboard/blob/master/CONTRIBUTING.md) for 
additional information.

### How can I help?
We have a [public project management board](https://github.com/orgs/PublicHealthEngland/projects/1) that 
shows outstanding issues to which everyone can contribute. Pick a ticket, assign it to 
yourself and move it to the **Doing** column, and you will be all set to start. There is 
also the [outstanding issues](https://github.com/PublicHealthEngland/coronavirus-dashboard-easy-read/issues) from 
which you can choose, but let us know that you are working on it so that multiple people 
don't end. up doing the same task.

No contribution is too small. We welcome help from everyone. Get in touch if you need 
additional information. We are here to help. 

## Cloning the code for re-deployment

### If your service isn’t on GOV.UK
You are welcome to use the GOV.UK patterns and frontend code even if your service isn’t 
considered part of GOV.UK. Although you will sometimes need to use different patterns, 
for example if you are building something like an admin interface.

While you can use the patterns, your site or service must not:

- identify itself as being part of GOV.UK
- use the crown or GOV.UK logotype in the header
- use the GDS Transport typeface
- suggest that it’s an official UK government website if it is not

These things are there to provide a consistent identity and navigation between GOV.UK and 
the sites and transactional services that hang off it. If your service isn’t on GOV.UK, 
there’s no need to maintain that identity - in fact, you might confuse or mislead people 
if you do.

You should also use the brand logo and font of your organisation.

Please consult the [GOV.UK Service Manual](https://www.gov.uk/service-manual/design/making-your-service-look-like-govuk#if-your-service-isnt-on-govuk) for 
additional information.

## Credits
This service is developed and maintained by [UK Health Security Agency](https://www.gov.uk/government/organisations/uk-health-security-agency).

---

Copyright (c) 2020-2021 UK Health Security Agency