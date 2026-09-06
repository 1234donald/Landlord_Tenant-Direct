**CHAPTER THREE**

**SYSTEM ANALYSIS AND DESIGN METHODOLOGY**

**3.1 Chapter Overview**

This chapter presents the system analysis and design methodology for the proposed **Online Platform for Direct Landlord-to-Tenant Contact Using Artificial Intelligence and Machine Learning Techniques**. The chapter translates the problems, requirements, research gaps and proposed solution identified in Chapters One and Two into a structured design for the development of the proposed system.

System analysis is concerned with examining the existing apartment-search process, identifying its major constituents, strengths and limitations, and determining the requirements that should be addressed by the proposed system. The analysis therefore considers the activities involved in searching for residential apartments, obtaining property information, communicating with landlords or intermediaries, inspecting properties and selecting suitable accommodation. The need for improved digital access to property information is particularly relevant in Nigeria, where research has identified the growing use of property-based websites while also reporting the continued importance of conventional real-estate marketing practices (Bamidele et al., 2018).

The proposed system is designed as a web-based platform that provides a centralised environment for prospective tenants, landlords and administrators. It combines apartment listing and search facilities with direct communication, administrative management, landlord verification and an intelligent apartment recommendation component.

The development of the system adopts **Agile Software Development Methodology**. Agile is appropriate because the proposed platform contains several functional components that can be developed incrementally, tested and refined as development progresses. Agile emphasises working software, responsiveness to changing requirements, continuous feedback and iterative delivery (Beck et al., 2001). Empirical studies have also identified iterative development, customer involvement and incremental delivery as important characteristics of Agile development, although Agile practices must be applied carefully to avoid problems such as insufficient requirements management and time pressure (Dybå & Dingsøyr, 2008; Meckenstock et al., 2024).

Within the Agile development methodology, **Object-Oriented Analysis and Design (OOAD)** is adopted as the system design approach. OOAD is suitable because the proposed system contains identifiable entities such as users, tenants, landlords, apartments, preferences, recommendations, messages and verification records. These entities can be represented as objects/classes and their relationships modelled using the Unified Modeling Language (UML). UML is widely used to represent software structure, behaviour and requirements, with class diagrams being particularly common in software engineering research (Koç et al., 2021).

The logical design presents the inputs, outputs and UML models of the system, including the use case diagram, activity diagram and class diagram. The physical design subsequently describes the program specification, database structure and system controls.

The machine-learning component of the proposed system uses a **Weighted K-Nearest Neighbour (Weighted KNN)** approach for apartment recommendation. The recommendation component compares tenant preferences with structured apartment attributes, applies feature weights and calculates a weighted distance between the tenant preference profile and available apartments. Neighbour-based methods are appropriate for similarity-based comparison, while feature weighting allows more important attributes to contribute more strongly to the distance calculation (Howe & Cardie, 1997). Recommender-system research also recognises the importance of representing user and item characteristics and supporting multi-criteria recommendation (Adomavicius & Tuzhilin, 2005).

The chapter therefore provides the design foundation for the implementation of the proposed system and the testing and evaluation activities presented in Chapter Four.

**3.2 System Analysis**

System analysis is the process of examining an existing system or process in order to understand its components, activities, strengths, weaknesses and requirements. The outcome of system analysis provides a basis for determining what the proposed system should accomplish and how it should improve upon the existing approach.

For this project, system analysis focuses on the process of finding residential apartments and establishing contact between prospective tenants and landlords. The analysis considers both traditional apartment-search practices and existing digital approaches.

**3.2.1 Analysis of the Existing System**

The existing apartment-search process involves a combination of traditional and digital methods. Traditionally, prospective tenants may search for apartments through personal contacts, referrals, estate agents, physical advertisements, roadside notices, social networks and direct visits to areas where apartments are available.

A prospective tenant may identify a property, obtain information about its rent and facilities, contact an agent or landlord, arrange an inspection, visit the apartment and subsequently determine whether the property satisfies his or her requirements.

Digital property platforms have improved access to property information by allowing prospective tenants to search for properties remotely. Research conducted among estate surveyors and valuers in Lagos found that property-based websites had been adopted as part of real-estate marketing, although conventional marketing methods remained significant (Bamidele et al., 2018).

Current Nigerian property platforms also demonstrate that online property search commonly involves listing information, search facilities, filtering and communication between property seekers and listing providers.

However, the availability of online listings does not automatically solve the problems of fragmented information, information quality, intermediary dependence or personalised apartment selection.

**3.2.1.1 Components of the Existing System**

The major constituents of the existing apartment-search system include the following:

1.  **Landlords** – individuals who own or manage residential properties available for rent.

2.  **Prospective Tenants** – individuals seeking residential accommodation that satisfies their requirements and financial capacity.

3.  **Estate Agents and Intermediaries** – persons who may facilitate communication between property owners and prospective tenants.

4.  **Property Advertisements** – information used to announce the availability and characteristics of apartments.

5.  **Property Information** – information relating to rent, location, apartment type, bedrooms, facilities and other characteristics.

6.  **Physical Inspection** – visits undertaken by prospective tenants to examine apartments before making rental decisions.

7.  **Communication Channels** – telephone calls, text messages, social-media communication and face-to-face interactions.

8.  **Informal Information Sources** – referrals, friends, relatives, neighbours and word-of-mouth information.

9.  **Online Property Platforms** – websites and other digital platforms through which property information can be displayed and searched.

The existence of these constituents shows that apartment searching is not a single activity but a sequence of interconnected activities involving property information, human interaction and decision-making.

**3.2.1.2 Strengths of the Existing System**

Despite its limitations, the existing apartment-search process has several strengths.

**Physical inspection provides direct observation of the property.** A prospective tenant can observe the physical condition, environment, accessibility and surrounding facilities of an apartment.

**Human interaction provides an opportunity for clarification.** Tenants can ask landlords or agents questions concerning rent, facilities, tenancy conditions and availability.

**Estate agents may provide local market knowledge.** Agents may know the locations of available properties and may help tenants identify alternatives.

**Traditional methods are familiar to users.** Individuals who may not be comfortable with technology can still search for apartments through conventional channels.

**Digital property platforms have increased accessibility.** Online property websites allow prospective tenants to access property information without necessarily visiting an agent's office. Research in Lagos has confirmed the increasing use of property-based websites in real-estate marketing (Bamidele et al., 2018).

**Online platforms can provide structured search facilities.** Digital property platforms can organise listings according to locations, property types, prices and other attributes, thereby reducing some of the effort associated with manual searching.

**3.2.1.3 Limitations of the Existing System**

The existing apartment-search process has several limitations that motivate the development of the proposed system.

1.  **Dependence on intermediaries:** Prospective tenants may have to rely on estate agents or other intermediaries before establishing direct contact with property owners.

2.  **Time-consuming search:** A tenant may have to inspect several apartments before identifying one that satisfies the required conditions.

3.  **Transportation and inspection costs:** Repeated physical visits may increase transportation expenses and consume considerable time.

4.  **Fragmented property information:** Apartment information may be distributed across agents, advertisements, social-media posts, websites and informal sources.

5.  **Inconsistent presentation of information:** Property advertisements may describe similar attributes using different formats, making comparison difficult.

6.  **Limited personalisation:** Conventional search mechanisms generally allow tenants to specify search criteria but do not necessarily calculate an overall similarity between tenant preferences and apartment characteristics.

7.  **Information-quality concerns:** An online listing does not by itself guarantee that all information supplied by a property advertiser is complete or accurate.

8.  **Limited intelligent ranking:** Conventional filtering may return properties satisfying individual criteria without considering the relative importance of several criteria simultaneously.

9.  **Intermediary-related costs:** Where estate agents are involved, prospective tenants may incur additional agency-related expenses.

10. **Limited integration:** Listing, searching, communication, administrative verification and intelligent recommendation may not be integrated into one system.

The limitations identified above demonstrate the need for a platform that combines structured property information, direct communication and personalised recommendation.

**3.2.2 Analysis of the Proposed System**

The proposed system is a web-based platform developed to provide a centralised environment where landlords can publish residential apartment information and prospective tenants can search for, compare and receive recommendations for potentially suitable apartments.

The proposed platform consists of three principal user categories:

- **Administrator**

- **Landlord**

- **Prospective Tenant**

The system also contains supporting functional components for apartment management, search and filtering, communication, verification, database management and machine-learning recommendation.

The proposed system differs from a conventional property-search platform primarily through the integration of the **Weighted KNN recommendation component**. Rather than merely displaying apartments based on manually selected filters, the system compares tenant preferences with apartment characteristics and ranks eligible apartments according to their calculated similarity.

This approach is appropriate for a system in which explicit user preferences and item characteristics are available. Recommender-system research identifies content and item characteristics as important inputs for recommendation and also highlights the usefulness of multi-criteria approaches where users have different preferences (Adomavicius & Tuzhilin, 2005).

**3.2.2.1 Components of the Proposed System**

The proposed system consists of the following major components.

**1. Tenant Module**

The tenant module enables prospective tenants to:

- register an account;

- log in securely;

- manage their profiles;

- search available apartments;

- apply search filters;

- view apartment details;

- specify apartment preferences;

- obtain ranked apartment recommendations;

- communicate with landlords; and

- manage relevant interactions.

**2. Landlord Module**

The landlord module enables landlords to:

- register;

- log in;

- manage their profiles;

- submit apartment listings;

- provide apartment information;

- upload supported apartment images;

- edit apartment listings;

- manage apartment availability; and

- communicate with prospective tenants.

**3. Administrator Module**

The administrator module provides administrative control over:

- users;

- landlords;

- apartment listings;

- landlord verification;

- system activities; and

- administrative reports.

The administrator's verification function is limited to the rules established by the platform. It does not constitute an automated legal determination of property ownership.

**4. Apartment Management Module**

This module manages:

- apartment location;

- rental price;

- apartment type;

- bedrooms;

- bathrooms;

- facilities;

- availability;

- descriptions; and

- supported multimedia information.

**5. Search and Filtering Module**

This module allows tenants to search and filter apartments using criteria such as:

- location;

- rental price;

- apartment type;

- bedrooms;

- bathrooms; and

- selected facilities.

**6. Recommendation Module**

The recommendation module represents the principal AI/ML component of the proposed system.

It:

- receives tenant preferences;

- retrieves available apartments;

- applies mandatory filters;

- transforms tenant and apartment information into comparable feature representations;

- normalises applicable numerical features;

- applies feature weights;

- calculates weighted distance;

- ranks apartments; and

- returns the highest-ranked apartments.

**7. Messaging Module**

The messaging module provides direct communication between landlords and prospective tenants.

**8. Database Management Module**

The database management component stores and retrieves:

- user information;

- landlord information;

- tenant preferences;

- apartment records;

- recommendations;

- messages; and

- verification records.

**3.2.2.2 Strengths of the Proposed System**

The proposed system provides the following strengths:

1.  **Direct landlord-to-tenant communication**, reducing dependence on an intermediary as the primary communication channel.

2.  **Centralised apartment information**, allowing property details to be accessed from one platform.

3.  **Structured property records**, allowing apartments to be represented using defined attributes.

4.  **Personalised recommendation**, allowing available apartments to be ranked according to tenant preferences.

5.  **Reduced search effort**, because the recommendation component can identify potentially suitable apartments from available listings.

6.  **Administrative management**, enabling system administrators to manage users and listings.

7.  **Landlord verification workflow**, providing an administrative review mechanism.

8.  **Web accessibility**, allowing the platform to be accessed through a web browser.

9.  **Modular implementation**, allowing individual components to be developed and tested separately.

10. **Machine-learning capability**, providing the intelligent recommendation functionality required by the project.

**3.2.2.3 Limitations of the Proposed System**

The proposed system has some limitations.

1.  **Internet dependence:** Users require internet connectivity to access the web-based system.

2.  **Data-quality dependence:** Recommendation quality depends on the completeness and accuracy of apartment information and tenant preferences.

3.  **Limited historical interaction data:** As an academic prototype, the system may not initially have sufficient historical user-interaction data for collaborative filtering. This supports the decision to use explicit tenant preferences and apartment characteristics.

4.  **Computational cost:** Weighted KNN requires distance calculations across candidate apartments. As the number of listings increases, the computational workload can increase.

5.  **Verification limitation:** Administrative verification cannot guarantee that every property-related claim supplied by a landlord is legally or factually correct.

6.  **Prototype limitation:** The proposed system is an academic project and therefore does not initially represent a full commercial real-estate marketplace.

7.  **Recommendation limitation:** The recommendation engine supports decision-making but does not make the final tenancy decision on behalf of the tenant.

**3.3 System Design**

System design translates the requirements identified during system analysis into a structured representation that can guide implementation.

The proposed system uses **Agile Software Development Methodology** as the overall development methodology and **Object-Oriented Analysis and Design (OOAD)** as the system design approach.

**Agile Development Methodology**

Agile Software Development is an iterative and incremental approach to software development that emphasises working software, continuous improvement, stakeholder feedback and responsiveness to changing requirements. The Agile Manifesto values working software, customer collaboration and responding to change, while its principles emphasise frequent delivery and regular reflection on the development process (Beck et al., 2001).

Agile is suitable for this project because the system consists of several modules that can be developed incrementally. The development can begin with essential functionality such as registration and authentication, followed by apartment listing, search, communication, recommendation and administration.

The proposed Agile development process consists of the following iterative activities:

**Requirement Identification → Planning → Design → Implementation → Testing → Review → Refinement → Next Iteration**

The iterations can be organised as follows:

**Iteration 1: Basic User Management**

The first iteration focuses on:

- user registration;

- login;

- authentication;

- user roles; and

- profile management.

**Iteration 2: Apartment Management**

The second iteration introduces:

- apartment registration;

- apartment listing;

- apartment editing;

- apartment deletion;

- availability; and

- apartment display.

**Iteration 3: Search and Filtering**

The third iteration implements:

- apartment search;

- location filtering;

- price filtering;

- apartment-type filtering; and

- other property filters.

**Iteration 4: Direct Communication**

The fourth iteration implements:

- landlord-tenant messaging;

- message storage;

- message retrieval; and

- communication management.

**Iteration 5: Recommendation Component**

The fifth iteration implements:

- tenant preference collection;

- feature preparation;

- normalisation;

- feature weighting;

- weighted distance calculation;

- K-neighbour selection; and

- recommendation ranking.

**Iteration 6: Administration and Verification**

The sixth iteration implements:

- landlord verification;

- user management;

- listing management;

- administrative monitoring; and

- reporting.

**Iteration 7: Integration and Evaluation**

The final iteration integrates the modules and conducts:

- functional testing;

- recommendation testing;

- usability checks;

- security checks; and

- overall system evaluation.

Agile is particularly suitable because changes discovered during testing can be incorporated into subsequent iterations rather than requiring the entire system to be redesigned. However, Agile does not eliminate the need for documentation and planning. Research has shown that Agile can experience problems when requirements, stakeholder involvement and delivery pressures are poorly managed (Meckenstock et al., 2024).

**Object-Oriented Analysis and Design**

OOAD is used as the **design approach**, not as the overall development methodology.

Object-oriented analysis identifies real-world entities in the problem domain and represents them as objects/classes with attributes, operations and relationships. Object-oriented design subsequently translates these conceptual models into a structure that can be implemented in software.

OOAD is appropriate for this project because the system contains identifiable entities such as:

- User;

- Tenant;

- Landlord;

- Administrator;

- Apartment;

- Preference;

- Recommendation;

- Message; and

- Verification.

UML provides a standard visual language for representing object-oriented systems. A systematic review of UML use in software engineering found that UML diagrams are commonly used for system design and modelling, with class diagrams among the most frequently used UML diagrams (Koç et al., 2021).

The object-oriented design of the proposed system therefore uses:

- Use Case Diagram;

- Activity Diagram; and

- Class Diagram.

These models describe system behaviour and structure before implementation.

**3.3.1 Logical Design**

Logical design describes what the system does and how information moves through the system without concentrating primarily on the physical implementation technologies.

The logical design of the proposed system includes:

- input design;

- output design;

- use case modelling;

- activity modelling; and

- class modelling.

**3.3.1.1 Input Design**

Input design defines the information entered into the system by tenants, landlords and administrators.

**User Registration Input**

The registration form accepts:

- full name;

- email address;

- password;

- user role; and

- contact information where applicable.

**Landlord Input**

A landlord provides:

- profile information;

- apartment location;

- rental price;

- apartment type;

- number of bedrooms;

- number of bathrooms;

- facilities;

- description;

- availability; and

- supported apartment images.

**Tenant Search Input**

The tenant may provide:

- preferred location;

- minimum or maximum price;

- apartment type;

- number of bedrooms;

- number of bathrooms; and

- selected facilities.

**Tenant Preference Input**

The recommendation component may receive:

- preferred location;

- maximum rental price;

- preferred apartment type;

- preferred number of bedrooms;

- preferred number of bathrooms;

- parking preference;

- electricity preference;

- water availability;

- security preference;

- furnished/unfurnished preference; and

- other supported facilities.

**Communication Input**

The messaging module receives:

- sender;

- receiver;

- message content; and

- message timestamp.

**Administrative Input**

The administrator may provide:

- verification decisions;

- listing-management decisions;

- user-management actions; and

- administrative report parameters.

Input validation will be applied to appropriate fields. OWASP recommends validating user input on the server side and checking both syntactic and semantic correctness before information is processed or stored.

**3.3.1.2 Output Design**

Output design specifies the information generated and presented by the system.

**Tenant Outputs**

The tenant can receive:

- available apartment listings;

- filtered search results;

- apartment details;

- ranked recommendations;

- permitted landlord information;

- messages;

- notifications; and

- profile information.

**Landlord Outputs**

The landlord can receive:

- listing status;

- apartment-management information;

- tenant messages;

- notifications; and

- administrative feedback.

**Administrator Outputs**

The administrator can receive:

- user records;

- landlord records;

- apartment records;

- verification status;

- administrative reports; and

- system activity information.

**Recommendation Output**

The principal intelligent output is the **ranked apartment recommendation list**.

The recommendation output should present relevant apartment information together with a ranking position and, where appropriate, a similarity/distance score.

The recommendation principle is:

**Smaller weighted distance → greater similarity → higher recommendation rank.**

**3.3.1.3 Use Case Diagram**

<img src="C:\Users\Mr Mark\Downloads\chapter-three-media/media/image1.png" style="width:6.68264in;height:8.01458in" alt="use_case_diagram" />**FIGURE 3:1 USE CASE DIAGRAM**

The use case diagram is split into 3 actors, the diagram represents the interactions between the major actors and the proposed system.

The three principal actors are:

1.  **Tenant**

2.  **Landlord**

3.  **Administrator**

**Tenant Use Cases**

<img src="C:\Users\Mr Mark\Downloads\chapter-three-media/media/image2.png" style="width:5.59861in;height:7.10903in" alt="tenant_use_case" />

FIGURE 3.6 TENANT USE CASE DIAGRAM

The tenant can:

- register;

- log in;

- manage profile;

- search apartments;

- apply filters;

- view apartment details;

- enter preferences;

- generate recommendations;

- contact landlords; and

- send/receive messages.

**Landlord Use Cases**

<img src="C:\Users\Mr Mark\Downloads\chapter-three-media/media/image3.png" style="width:5.74514in;height:6.88611in" alt="landlord_use_case" />

**FIGURE 3.7 LANDLORD USE CASE DIAGRAM**

The landlord can:

- register;

- log in;

- manage profile;

- create apartment listings;

- edit apartment listings;

- manage listing availability;

- delete permitted listings; and

- send/receive messages.

**Administrator Use Cases**

<img src="C:\Users\Mr Mark\Downloads\chapter-three-media/media/image4.png" style="width:5.23333in;height:6.96806in" alt="administrator_use_case" />

**FIGURE 3.8 ADMINISTRATOR USE CASE**

The administrator can:

- log in;

- manage users;

- review landlord information;

- approve or reject landlord submissions;

- manage apartment listings;

- monitor the system; and

- generate administrative reports.

The recommendation relationship can be represented as:

**Enter Preferences → Generate Recommendations → View Ranked Apartments**

The recommendation process accesses apartment information stored in the database.

<img src="C:\Users\Mr Mark\Downloads\chapter-three-media/media/image5.png" style="width:6.65347in;height:8.00556in" alt="activity_diagram" />**3.3.1.4 Activity Diagram**

**FIGURE 3.2 ACTIVITY DIAGRAM**

**3.3.1.4: Activity Diagram for Apartment Search and Recommendation**

The activity diagram represents the sequence of activities involved in the apartment-search and recommendation process.

The process begins when a tenant logs into the platform and selects the apartment-search or recommendation function.

The activity sequence is:

1.  Tenant logs in.

2.  Tenant enters apartment preferences.

3.  System validates the preferences.

4.  System retrieves available apartments.

5.  System applies mandatory filters.

6.  System represents tenant preferences as a feature vector.

7.  System represents apartment records as feature vectors.

8.  Categorical variables are encoded.

9.  Numerical variables are normalised.

10. Feature weights are applied.

11. Weighted distance is calculated.

12. Candidate apartments are ranked.

13. The highest-ranked apartments are selected.

14. Recommendations are displayed to the tenant.

15. Tenant may view apartment details.

16. Tenant may contact the landlord.

Where a tenant specifies a mandatory maximum rental price, for example, an apartment exceeding the specified maximum may be removed before the similarity calculation.

This distinction separates **hard constraints** from **similarity-based ranking**.

**3.3.1.5 Class Diagram**

<img src="C:\Users\Mr Mark\Downloads\chapter-three-media/media/image6.png" style="width:8.46597in;height:7.61736in" alt="class_diagram" />

**FIGURE 3.8 CLASS DIAGRAM**

**3.3.1.5: Class Diagram of the Proposed System**

The class diagram represents the static structure of the proposed system.

**User Class**

**Attributes**

- user_id;

- full_name;

- email;

- password;

- role;

- contact; and

- date_created.

**Tenant Class**

**Attributes**

- tenant_id;

- user_id; and

- profile information.

**Landlord Class**

**Attributes**

- landlord_id;

- user_id;

- verification_status; and

- profile information.

**Administrator Class**

**Attributes**

- administrator_id;

- user_id; and

- administrative privileges.

**Apartment Class**

**Attributes**

- apartment_id;

- landlord_id;

- location;

- rent_amount;

- apartment_type;

- bedrooms;

- bathrooms;

- facilities;

- description; and

- availability.

**Preference Class**

**Attributes**

- preference_id;

- tenant_id;

- preferred_location;

- maximum_price;

- apartment_type;

- bedrooms;

- bathrooms; and

- facilities.

**Recommendation Class**

**Attributes**

- recommendation_id;

- tenant_id;

- apartment_id;

- distance_score;

- ranking; and

- date_created.

**Message Class**

**Attributes**

- message_id;

- sender_id;

- receiver_id;

- message_content;

- timestamp; and

- status.

**Verification Class**

**Attributes**

- verification_id;

- landlord_id;

- administrator_id;

- status;

- verification_date; and

- remarks.

The major relationships include:

- A User may be associated with a Tenant, Landlord or Administrator role.

- A Landlord can manage multiple Apartments.

- A Tenant can have one or more Preference records.

- A Tenant can receive multiple Recommendation records.

- An Apartment can appear in recommendations for multiple tenants.

- Users can send and receive Messages.

- An Administrator can process Verification records for landlords.

**3.3.2 Physical Design**

Physical design describes how the logical system will be implemented using specific programming technologies, database structures, system modules and security controls.

The proposed system is a web application implemented using:

- **Python** as the principal programming language;

- **Django** as the web application framework;

- **PostgreSQL** as the relational database management system;

- **HTML, CSS and JavaScript** for the user interface;

- **Python-based machine-learning functionality** for Weighted KNN; and

- a standard web browser for system access.

Django is appropriate for the proposed platform because it provides facilities for developing web applications, including an object-relational mapping layer, authentication functionality and administrative capabilities.

PostgreSQL is used as the relational database because it provides tables, relationships, constraints, foreign keys and transaction-related capabilities required for structured application data.

**3.3.2.1 Program Specification**

The program is divided into functional modules.

**A. User Management Module**

This module manages:

- registration;

- login;

- authentication;

- role assignment;

- profile management; and

- session management.

Django provides built-in facilities for user authentication and account management, reducing the need to implement fundamental authentication mechanisms entirely from scratch.

**B. Landlord Management Module**

The landlord module manages:

- landlord registration;

- landlord profiles;

- verification status;

- landlord apartment listings; and

- landlord communication.

**C. Apartment Management Module**

This module handles:

- apartment creation;

- apartment editing;

- apartment deletion;

- apartment descriptions;

- facilities;

- images;

- availability; and

- listing management.

**D. Search and Filtering Module**

This module allows tenants to:

- search apartments;

- specify criteria;

- filter listings;

- view apartment details; and

- identify apartments satisfying mandatory conditions.

**E. Recommendation Module**

The recommendation module is the **principal AI/ML component** of the system.

It performs the following operations:

1.  collect tenant preferences;

2.  validate preference information;

3.  retrieve available apartments;

4.  apply mandatory filters;

5.  represent tenant preferences as feature vectors;

6.  represent apartments as feature vectors;

7.  encode categorical attributes;

8.  normalise numerical attributes;

9.  assign feature weights;

10. calculate weighted distances;

11. identify the nearest candidate apartments;

12. rank the candidate apartments; and

13. display the recommendations.

**Weighted KNN Model**

Let the tenant preference profile be:

``` math
\text{U=}\left( \text{u}_{\text{1}},\text{u}_{\text{2}},\text{u}_{\text{3}},\text{…},\text{u}_{\text{n}} \right)\text{
}
```

and an apartment be represented as:

``` math
\text{A}_{\text{j}}\text{=}\left( \text{a}_{\text{j1}},\text{a}_{\text{j2}},\text{a}_{\text{j3}},\text{…},\text{a}_{\text{jn}} \right)\text{
}
```

where:

- $`\text{U}`$represents the tenant's preference vector;

- $`\text{A}_{\text{j}}`$represents apartment $`\text{j}`$;

- $`\text{u}_{\text{i}}`$represents the tenant's preferred value for feature $`\text{i}`$;

- $`\text{a}_{\text{ji}}`$represents apartment $`\text{j}`$'s value for feature $`\text{i}`$; and

- $`\text{n}`$represents the number of features.

The weighted Euclidean distance is calculated as:

``` math
\text{D}_{\text{w}}\left( \text{U},\text{A}_{\text{j}} \right)\text{=}\sqrt{\sum_{\text{i=1}}^{\text{n}}\text{w}_{\text{i}}\left( \text{u}_{\text{i}}\text{−}\text{a}_{\text{ji}} \right)^{\text{2}}}\text{
}
```

where $`\text{w}_{\text{i}}`$represents the weight assigned to feature $`\text{i}`$.

Feature weighting allows more important attributes to contribute more strongly to the similarity calculation. Research on KNN feature weighting demonstrates that assigning different importance to features can reduce the effect of less relevant features and improve nearest-neighbour performance (Howe & Cardie, 1997).

The recommendation process therefore does not treat all apartment characteristics as necessarily equally important.

For example, if a tenant identifies rental price and location as highly important while parking is less important, the corresponding feature weights can reflect those priorities.

**Feature Normalisation**

Numerical attributes may have substantially different scales. Rental price, for example, may have values in hundreds of thousands of naira, whereas bedrooms may have values such as 1, 2, 3 or 4.

To prevent large numerical scales from dominating the distance calculation, numerical features can be normalised using min-max normalisation:

``` math
\text{x}^{\text{'}}\text{=}\frac{\text{x−}\text{x}_{\text{min}}}{\text{x}_{\text{max}}\text{−}\text{x}_{\text{min}}}\text{
}
```

where:

- $`\text{x}`$is the original value;

- $`\text{x}^{\text{'}}`$is the normalised value;

- $`\text{x}_{\text{min}}`$is the minimum value; and

- $`\text{x}_{\text{max}}`$is the maximum value.

**Categorical Features**

Categorical attributes such as apartment type may be transformed into numerical representations before the distance calculation.

For example:

| Apartment Type | Encoded Representation |
|:---------------|------------------------|
| Self-contained | 1                      |
| Mini-flat      | 2                      |
| Flat           | 3                      |
| Duplex         | 4                      |

Table

Where categorical variables do not have a meaningful ordinal relationship, an appropriate encoding such as one-hot encoding should instead be used. This prevents the numerical representation from incorrectly implying that one category is inherently closer to another.

**K-Value**

The value of $`\text{K}`$represents the number of nearest candidate apartments considered by the recommendation process.

For example:

``` math
\text{K=5}
```

means that the five closest candidate apartments can constitute the recommendation set.

The final value of $`\text{K}`$should be selected during implementation and evaluation rather than being arbitrarily fixed without testing.

**Recommendation Ranking**

After calculating the weighted distance for eligible apartments, the system sorts the results in ascending order.

Therefore:

``` math
\text{D}_{\text{w}}\left( \text{U},\text{A}_{\text{1}} \right)\text{<}\text{D}_{\text{w}}\left( \text{U},\text{A}_{\text{2}} \right)\text{
}
```

means that apartment $`\text{A}_{\text{1}}`$is more similar to the tenant's preference profile than apartment $`\text{A}_{\text{2}}`$.

The recommendation principle is therefore:

**Smallest distance → highest similarity → highest recommendation rank.**

This makes the recommendation component a genuine machine-learning/similarity-based component rather than merely a manually programmed filtering rule.

**F. Messaging Module**

The messaging module supports direct communication between tenants and landlords.

The module manages:

- sender;

- receiver;

- message content;

- timestamp; and

- message status.

**G. Administration Module**

The administration module manages:

- users;

- landlords;

- apartment listings;

- verification;

- monitoring; and

- reports.

**H. Landlord Verification Module**

The landlord verification process follows:

**Registration → Information Submission → Pending Review → Administrator Review → Approval/Reject Decision → Verification Status**

The system records the administrative decision.

Importantly, this verification function does **not** mean that the system automatically determines legal ownership of property, validates government land documents or makes legal decisions.

The verification feature is an administrative control for managing information submitted to the platform.

**3.3.2.2 Layout of Tables Design and Database Structure**

The proposed system uses a relational database. PostgreSQL is appropriate for the design because relational data is stored in tables containing rows and columns, while relationships between tables can be represented through keys and constraints.

**Table 3.1: Users Table**

| Field        | Data Type | Description                       |
|:-------------|-----------|-----------------------------------|
| user_id      | Integer   | Unique user identifier            |
| full_name    | Varchar   | User's full name                  |
| email        | Varchar   | User email address                |
| password     | Varchar   | Hashed password                   |
| role         | Varchar   | Tenant, Landlord or Administrator |
| contact      | Varchar   | Contact information               |
| date_created | DateTime  | Account creation date             |

**Table 3.2: Apartments Table**

| Field          | Data Type | Description                 |
|:---------------|-----------|-----------------------------|
| apartment_id   | Integer   | Unique apartment identifier |
| landlord_id    | Integer   | Associated landlord         |
| location       | Varchar   | Apartment location          |
| rent_amount    | Decimal   | Rental price                |
| apartment_type | Varchar   | Type of apartment           |
| bedrooms       | Integer   | Number of bedrooms          |
| bathrooms      | Integer   | Number of bathrooms         |
| facilities     | Text      | Available facilities        |
| description    | Text      | Apartment description       |
| availability   | Boolean   | Availability status         |

**Table 3.3: Tenant Preferences Table**

| Field          | Data Type | Description                  |
|:---------------|-----------|------------------------------|
| preference_id  | Integer   | Unique preference identifier |
| tenant_id      | Integer   | Associated tenant            |
| location       | Varchar   | Preferred location           |
| maximum_price  | Decimal   | Maximum rental budget        |
| apartment_type | Varchar   | Preferred apartment type     |
| bedrooms       | Integer   | Preferred bedrooms           |
| bathrooms      | Integer   | Preferred bathrooms          |
| facilities     | Text      | Preferred facilities         |

**Table 3.4: Recommendations Table**

| Field             | Data Type | Description               |
|:------------------|-----------|---------------------------|
| recommendation_id | Integer   | Recommendation identifier |
| tenant_id         | Integer   | Associated tenant         |
| apartment_id      | Integer   | Recommended apartment     |
| distance_score    | Float     | Weighted distance         |
| ranking           | Integer   | Recommendation position   |
| date_created      | DateTime  | Recommendation date       |

**Table 3.5: Messages Table**

| Field           | Data Type | Description               |
|:----------------|-----------|---------------------------|
| message_id      | Integer   | Unique message identifier |
| sender_id       | Integer   | Message sender            |
| receiver_id     | Integer   | Message receiver          |
| message_content | Text      | Message body              |
| timestamp       | DateTime  | Time sent                 |
| status          | Varchar   | Message status            |

**Table 3.6: Verification Table**

| Field             | Data Type | Description                     |
|:------------------|-----------|---------------------------------|
| verification_id   | Integer   | Verification identifier         |
| landlord_id       | Integer   | Landlord being reviewed         |
| administrator_id  | Integer   | Administrator conducting review |
| status            | Varchar   | Pending, Approved or Rejected   |
| remarks           | Text      | Administrative remarks          |
| verification_date | DateTime  | Date of decision                |

**Database Relationships**

The principal relationships are:

1.  One user account is associated with one principal role: Tenant, Landlord or Administrator.

2.  One landlord can have multiple apartment listings.

3.  One tenant can have one or more preference records.

4.  One tenant can receive multiple recommendation records.

5.  One apartment can appear in recommendations for multiple tenants.

6.  One user can send multiple messages.

7.  One user can receive multiple messages.

8.  A landlord can have a verification record managed by an administrator.

9.  Recommendation records reference both tenants and apartments.

10. Foreign keys are used to maintain relationships between related records.

**3.3.2.2: Entity Relationship Diagram of the Proposed Database**

<img src="C:\Users\Mr Mark\Downloads\chapter-three-media/media/image7.png" style="width:8.50139in;height:7.62708in" alt="er_diagram" />

FIGURE 3.4 ENTITY RELATIONSHIP DIAGRAM

**3.3.2.3 System Controls**

System controls are mechanisms designed to improve the security, accuracy, consistency and reliability of the proposed system.

**A. Security Controls**

The system will implement:

- secure authentication;

- password hashing;

- session management;

- role-based access control;

- protected administrative functions;

- controlled access to user information;

- input validation;

- secure handling of uploaded files; and

- logging of important administrative actions.

Authentication should verify the identity of a user, while authorisation determines what that user is permitted to access. OWASP recommends strong authentication practices, secure password handling and appropriate session management for web applications.

**B. Input Controls**

Input controls will include:

- required-field validation;

- email validation;

- password validation;

- numeric validation;

- rental-price range validation;

- bedroom and bathroom validation;

- apartment-type validation;

- preference validation;

- duplicate checks where appropriate; and

- server-side validation.

Server-side validation is particularly important because client-side validation can be bypassed. OWASP recommends validating input on the server before it is processed.

**C. Role-Based Access Control**

The system will restrict functions according to user roles.

For example:

- tenants cannot access administrator functions;

- landlords cannot approve their own verification;

- administrators can manage users and listings;

- tenants can manage their own preferences;

- landlords can manage their own listings;

- users cannot access another user's private account information without authorisation.

Access control should follow the principle of least privilege, whereby users receive only the permissions necessary to perform their authorised functions.

**D. Listing Controls**

Apartment listings will be controlled through:

- mandatory field validation;

- availability status;

- listing ownership;

- editing restrictions;

- deletion restrictions;

- administrator oversight; and

- appropriate display controls.

**E. Verification Controls**

The landlord verification workflow is:

**Landlord Registration**

↓

**Landlord Information Submitted**

↓

**Pending Verification**

↓

**Administrator Review**

↓

**Decision**

↙︎　　　　　　　　　↘︎

**Rejected**　　　　 **Approved**

↓

**Verification Status Updated**

The system stores the verification status and relevant administrative remarks.

The verification process is an administrative mechanism and **not a legal property-ownership verification mechanism**.

**F. Recommendation Controls**

The recommendation component will implement the following controls:

1.  validate tenant preferences;

2.  retrieve available apartments;

3.  apply mandatory constraints;

4.  encode categorical attributes;

5.  normalise numerical features;

6.  apply feature weights;

7.  calculate weighted distances;

8.  identify the nearest candidates;

9.  rank the apartments;

10. return the specified number of recommendations.

The system should also handle situations where no apartment satisfies the mandatory conditions. In such cases, the system should inform the tenant that no suitable apartment was found rather than generating misleading recommendations.

**G. Output Controls**

Output controls will regulate:

- apartment information displayed to tenants;

- recommendation results;

- landlord information;

- administrative reports;

- user-specific information;

- messages; and

- verification information.

Only information appropriate to the user's role should be displayed.

**H. Database Controls**

Database controls will include:

- primary keys;

- foreign keys;

- appropriate data types;

- uniqueness constraints;

- required fields;

- referential integrity;

- controlled deletion;

- transaction management where required; and

- database backup procedures.

PostgreSQL supports relational tables, foreign keys, constraints and transaction-related features that are appropriate for structured web application data.

**I. Audit Controls**

Where applicable, the system will record:

- login activities;

- administrative activities;

- landlord verification decisions;

- listing-management activities; and

- other important system events.

These records can support troubleshooting, accountability and system monitoring.

**3.3.2.4 Overall System Design Flow**

The complete design and development relationship is represented as:

<img src="C:\Users\Mr Mark\Downloads\chapter-three-media/media/image8.png" style="width:6.70417in;height:7.56389in" alt="overall_system_design_workflow" />

FIGURE 3.5 OVERALL SYSTEM DESIGN FLOW

**Traceability Between Objectives and System Design**

The system design is aligned with the project objectives as follows:

| Project Objective | Corresponding System Design |
|:---|----|
| Design an online platform for registration and management of residential apartment listings | User Management Module, Landlord Module, Apartment Management Module |
| Develop a system through which prospective tenants can register, search and access structured property information | Tenant Module, Search and Filtering Module, Apartment Database |
| Provide direct communication between landlords and prospective tenants | Messaging Module |
| Implement administrative functionality for managing users and apartment listings | Administrator Module, Listing Controls |
| Implement an ML-based apartment recommendation component | Weighted KNN Recommendation Module |
| Design a structured database for system information | PostgreSQL database, relational tables and database relationships |
| Test and evaluate the developed system | Functional modules, recommendation outputs and system controls provide testable components for Chapter Four |

This traceability ensures that the system design does not introduce major functionality unrelated to the stated project objectives.

**3.4 Chapter Summary**

This chapter presented the system analysis and design methodology for the proposed **Online Platform for Direct Landlord-to-Tenant Contact Using Artificial Intelligence and Machine Learning Techniques**.

The existing apartment-search process was analysed by identifying its constituents, strengths and limitations. The analysis showed that conventional apartment searching can involve intermediary dependence, physical inspection, fragmented property information, transportation costs, inconsistent information presentation and limited personalisation. Nigerian research has also demonstrated the increasing role of property-based websites in real-estate marketing while indicating that conventional practices remain important (Bamidele et al., 2018).

The proposed system was subsequently analysed. Its major constituents are the Tenant Module, Landlord Module, Administrator Module, Apartment Management Module, Search and Filtering Module, Recommendation Module, Messaging Module and Database Management Module.

The chapter adopted **Agile Software Development Methodology** as the overall development methodology. Agile was selected because the proposed system can be developed incrementally through iterations involving requirements, design, implementation, testing, review and refinement. This is consistent with the Agile emphasis on frequent delivery, working software and responsiveness to change (Beck et al., 2001; Dybå & Dingsøyr, 2008).

Within Agile, **Object-Oriented Analysis and Design (OOAD)** was adopted as the system design approach. OOAD was considered appropriate because the proposed platform contains identifiable entities such as users, tenants, landlords, apartments, preferences, recommendations, messages and verification records. UML use case, activity and class diagrams were therefore used to represent system behaviour and structure.

The logical design presented the system inputs and outputs and described the use case, activity and class diagrams. The physical design described the program specification, database structure and system controls. Python and Django were selected for application development, while PostgreSQL was selected for relational data storage. Django provides web-development and authentication facilities, while PostgreSQL provides relational database functionality.

The chapter also defined the **Weighted KNN recommendation component**, which constitutes the principal machine-learning functionality of the proposed system. Tenant preferences and apartment characteristics are represented as feature vectors. Applicable categorical variables are encoded, numerical variables are normalised, feature weights are applied and weighted distances are calculated. The apartments are subsequently ranked according to their distance from the tenant's preference profile.

The chapter further established system controls covering security, authentication, input validation, role-based access, listing management, landlord verification, recommendation processing, output management and database integrity. These controls provide the foundation for secure and reliable implementation.

Overall, the chapter provides the design foundation for implementing the proposed system and for conducting the testing and evaluation activities presented in Chapter Four.

**REFERENCES**

Adomavicius, G., & Tuzhilin, A. (2005). Toward the next generation of recommender systems: A survey of the state-of-the-art and possible extensions. *IEEE Transactions on Knowledge and Data Engineering, 17*(6), 734–749. [<u>https://doi.org/10.1109/TKDE.2005.99</u>](https://doi.org/10.1109/TKDE.2005.99)

Bamidele, A. O., Adenusi, R. D., & Osunsanmi, T. O. (2018). Towards improved performance in marketing: The use of property-based websites by estate surveyors and valuers in Lagos, Nigeria. *Journal of African Real Estate Research, 3*(1), 81–93. https://doi.org/10.15641/jarer.v1i1.451

Dybå, T., & Dingsøyr, T. (2008). Empirical studies of agile software development: A systematic review. *Information and Software Technology, 50*(9–10), 833–859. [<u>https://doi.org/10.1016/j.infsof.2008.01.006</u>](https://doi.org/10.1016/j.infsof.2008.01.006)

Howe, N. R., & Cardie, C. (1997). Examining the impact of feature weighting schemes on k-nearest neighbor classification. *Proceedings of the AAAI-97 Workshop on Relevance*.

Koç, H., Erdoğan, A. M., Barjakly, Y., & Peker, S. (2021). UML diagrams in software engineering research: A systematic literature review. *Proceedings, 74*(1), 13. [<u>https://doi.org/10.3390/proceedings2021074013</u>](https://doi.org/10.3390/proceedings2021074013?utm_source=chatgpt.com)

Meckenstock, J.-N., et al. (2024). Shedding light on the dark side – A systematic literature review of the issues in agile software development methodology use. *Journal of Systems and Software, 211*, 111966.

Ogundipe, K. E., Owolabi, J. D., Ogunbayo, B. F., & Aigbavboa, C. O. (2024). Exploring inhibiting factors to affordable housing provision in Lagos metropolitan city, Nigeria. *Frontiers in Built Environment, 10*. [<u>https://doi.org/10.3389/fbuil.2024.1408776</u>](https://doi.org/10.3389/fbuil.2024.1408776)

Moore, E. A. (2019). Addressing housing deficit in Nigeria: Issues, challenges and prospects. *CBN Economic and Financial Review, 57*(4), 201–222.

Rath, S. P., Jain, N. K., Tomer, G., & Singh, A. K. (2025). A systematic literature review of agile software development projects. *Information and Software Technology, 182*, 107727. https://doi.org/10.1016/j.infsof.2025.107727

Budgen, D., Burn, A. J., Brereton, O. P., Kitchenham, B. A., & Pretorius, R. (2011). Empirical evidence about the UML: A systematic literature review. *Software: Practice and Experience*. https://doi.org/10.1002/spe.1009

Sien, V. Y. (2011). An investigation of difficulties experienced by students developing unified modelling language (UML) class and sequence diagrams. *Computer Science Education, 21*(4), 317–342. https://doi.org/10.1080/08993408.2011.630127

Gemino, A., & Parker, D. (2009). Use case diagrams in support of use case modeling: Deriving understanding from empirical studies. *Journal of Database Management*.

Agile Manifesto Authors. (2001). *Manifesto for Agile software development*. [Agile Manifesto official website](https://agilemanifesto.org/?utm_source=chatgpt.com)

Django Software Foundation. (2026). *Django documentation and overview*. [Django official documentation](https://www.djangoproject.com/start/overview/?utm_source=chatgpt.com)

PostgreSQL Global Development Group. (2026). *PostgreSQL documentation*. [PostgreSQL official documentation](https://www.postgresql.org/docs/current/?utm_source=chatgpt.com)

OWASP Foundation. (2026). *Input validation cheat sheet*. [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html?utm_source=chatgpt.com)

OWASP Foundation. (2026). *Authentication cheat sheet*. [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html?utm_source=chatgpt.com)

Larman, C. (2004). *Applying UML and patterns: An introduction to object-oriented analysis and design and iterative development* (3rd ed.). Upper Saddle River, NJ: Prentice Hall.

Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9th ed.). New York, NY: McGraw-Hill.

Sommerville, I. (2016). *Software engineering* (10th ed.). Boston, MA: Pearson.
