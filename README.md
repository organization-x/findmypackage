# Find My Package (Incubator 2022)

### FMP - All-in-One Website, where you can track your packages

## Overview

### Goal

As part of the 2022 incubator hosted by AI Camp, we (a group of highschool students), have come together to create an all-in-one package tracking website, that tells an individual all the important details regarding their package location and delivery time. Our website is tailored for the average person, who would like to know the essentials, while not having the additional, less important and complicated information clutter the screen. Our platform implements new features such as a visual map of the package location and an adjusted ETA dependent on any global events that may affect shipping. Our goal is to make package tracking straight forward and visually aiding, while making it as functional and accurate as possible.

### Code

#### Frontend

Our website was outlined in brief with [Figma](https://www.figma.com/), linked [here](https://www.figma.com/file/JSULGHeTbNlblRTeW8jWoK/FindMyPackageMockup?node-id=27%3A1973), and later written with HTML and CSS from scratch. For functionality of the review section on the website we used [JavaScript](https://www.javascript.com/)

#### Backend

Our team implemented the 4 most popular and common shpping couriers used: [UPS](https://www.ups.com/), [USPS](https://www.usps.com/), [FedEx](https://www.fedex.com/), and [DHL](https://www.dhl.com/). To implement these couriers into our product, we used [Django](https://www.djangoproject.com/), a python based framework. To create a database storing reviews from the users, we used [SQLite](https://www.sqlite.com/) during local development and [PostgreSQL](https://www.postgresql.org/) during deployment.

### Pages

- Track
  - Initial landing page for users
    - Users can enter in their tracking number
    - Displays about section, detailing product and it's purpose
- My Package (not shown in navbar)
  - Resulting page of user entering their tracking number
  - Displays package location on a map and provides tracking information
- FAQs
  - Displays frequently asked questions about our product
- Our Team
  - Insight on our team members and our contact information
- Reviews
  - Displays past reviews and allows users to write their own reviews and give us feedback