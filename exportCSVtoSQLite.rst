How to import a CSV file from SQLite
====================================

Step 1
------

Create a new database using SQLite command line tool::

    $sqlite3 newdb.db

this leads us to a new promtp where we're going to execute the next steps.

Step 2
------

Define the field separator that is being used in the CSV file e.g.::

    sqlite> .separator ;

usually fields are separated by a colon or a semicolon.

Step 3
------

Create a new table with the same number of fields that our CSV file and choose
a suitable type for them, if my table has 5 fields then it should look like this::

    sqlite> CREATE TABLE MyTable (id int not null, name varchar(50) not null, lastname varchar(50), email varchar(50) not null, session varchar(20) not null);

this will create my new table so we finish with the next step

Step 4
------

Import all the tables information from the CSV file to our new table, if we
are positioned in the folder that contains the CSV file then::

    sqlite> .import ./MyCSVfile.csv MyTable

If everything is ok in the CSV file all go smoothly =)
