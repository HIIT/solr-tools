# Solr-tools

These instructions should help you set up your own instance of the
Solr search engine and this repository provides some scripts to help
import data into your new Solr instance.

## Install Solr

As of this writing the newest version of Solr is 5.3, but you can
check from the [Solr web site][1] if there is a newer version and
change the commands below accordingly.

    wget http://www.nic.funet.fi/pub/mirrors/apache.org/lucene/solr/5.3.0/solr-5.3.0.tgz
    tar xvf solr-5.3.0.tgz 

### Run Solr directly (Linux and OS X)

Solr can now be started with:

    ./solr-5.3.0/bin/solr start
    
It should now be up and running, just go to <http://localhost:8983> to check it out.

Solr can be stopped with:

    ./solr-5.3.0/bin/solr stop -all

and the current status can be checked with:

    ./solr-5.3.0/bin/solr status

### Install and auto-start Solr (Linux only)

    umask 022
    sudo ./solr-5.3.0/bin/install_solr_service.sh solr-5.3.0.tgz 

The `umask` is just to make sure the installation will be readable for
all users. After this Solr should already be up and running, just go
to <http://localhost:8983> to check it out.

In the future you can start and stop Solr in the normal way:

    sudo service solr start
    sudo service solr stop

The Solr files have been installed in the `/opt/solr` directory, for
example the executable binaries can be found in `/opt/solr/bin`.

## Importing Wikipedia

For importing from a Wikipedia XML dump there exists a ready-made
configuration to make things easier. First you need to edit the files
in the
[`wikipedia_config`](https://github.com/HIIT/solr-tools/tree/master/wikipedia_config)
directory that you get when checking out this repository. In
particular change the `url` to the correct location of the
`enwiki-latest-pages-articles.xml` file in
[`arxiv_config/conf/data-config.xml`](https://github.com/HIIT/solr-tools/blob/master/wikipedia_config/conf/data-config.xml).

Once you are done you can initialise the core in Solr:

    sudo -u solr /opt/solr/bin/solr create_core -c enwiki -d ~/solr-tools/wikipedia_config

After this you can start importing the data by going to the web UI at
<http://localhost:8983/solr/#/enwiki/dataimport> and press Execute.

If you mess everything up and wish to delete everything from the core you can run:

    curl http://localhost:8983/solr/enwiki/update?commit=true -d '<delete><query>*:*</query></delete>'

For other data sets you have to do things the more complicated way.
Read below for more detailed information.

## Create a new database in Solr

First you have to decide if you want to use a fixed schema for the
database, or use the new schemaless mode. A schema is a description of
the fields and data types of each record in the database, together
with information on how they are processed and indexed. For more
serious work you probably want to use a schema. However, we will first
describe how to setup a schemaless database, this is useful for
testing and learning Solr when you want to get started quickly.

### Setup without schema

Let's create a new database named `arxiv-cs`. You have to run the
create command as the `solr` user like this:

    sudo -u solr /opt/solr/bin/solr create_core -c arxiv-cs -d data_driven_schema_configs

This creates a new core, which is the Solr term for a database. You
can have many cores in the same Solr instance. The `-c arxiv-cs`
option gives a name to the core, you can of course give it any name
you want. The `-d data_driven_schema_configs` option means that you do
not need to specify a schema for the database, but that it will derive
it automatically from the uploaded data.

### Setup with schema

In this section we will setup a database with schema. Note that this
is an alternative to the schemaless setup described in the previous
section. (You can try them both at the same time, but then you have to
give them different names.)

To make your life easier I have created a directory with the starting
point already configured for arXiv data in the directory
[`arxiv_config`](https://github.com/HIIT/solr-tools/tree/master/arxiv_config).
The file
[`arxiv_config/conf/schema.xml`](https://github.com/HIIT/solr-tools/blob/master/arxiv_config/conf/schema.xml)
is the most important file which sets the schema. The
[format is documented in the Solr wiki][2], but it isn't too hard to
understand by just looking at the existing file as an example.

For example:

    <field name="title" type="text_en" indexed="true" stored="true"/>

creates a field called "title" which will contain English text
(`text_en`), and which is indexed and stored in the database (for huge
data fields you might only want to have them indexed but not stored as
such). The `text_en` field type is defined later in `schema.xml` in a
`<fieldType>` declaration. You can see that it specifies a tokenizer,
stop word filtering, and Porter stemming among other things.

This example:

    <field name="keyword" type="text_general" indexed="true" stored="true" multiValued="true"/>

creates a "keyword" field of the type `text_general` (again check the
definition later in the file). The most interesting thing here is the
`multiValued="true"` part which specifies that you can give multiple
keywords in your data.

Then:

    <field name="text" type="text_en" indexed="true" stored="false" multiValued="true" />
    <copyField source="title" dest="text"/>
    <copyField source="author" dest="text"/>
    <copyField source="abstract" dest="text"/>

sets up a field "text" to which title, author and abstract fields are
copied to. This is a special field that is used as the default target
for text searches. You can also search the other indexed field, but
they have to be targetted explicitly.

Finally, after you have made any changes to the schema you can create
the new database (Solr core):

    sudo -u solr /opt/solr/bin/solr create_core -c arxiv-cs-s -d ~/solr-tools/arxiv_config

Here you might have to change the last argument to match the path
where you have cloned this repository.

## Fetch and import data to Solr

In this git repository are some example scripts to get data from arXiv
and convert them to Solr's format. You can modify these scripts to
work for your own data format. In short the final XML format for
uploading to Solr looks a bit like this:

    <add>
      <doc>
        <field name="id">oai:arXiv.org:0704.0002</field>
        <field name="last_modified">2008-12-13T00:00:00Z</field>
        <field name="set">cs</field>
        <field name="title">Sparsity-certifying Graph Decompositions</field>
        <field name="author">Streinu, Ileana</field>
        <field name="author">Theran, Louis</field>
        <field name="subject">Mathematics - Combinatorics</field>
        <field name="abstract">We describe a new algorithm, etc etc</field>
        <field name="comment">To appear in Graphs and Combinatorics</field>
        <field name="keyword">algorithmic solutions</field>
        <field name="keyword">graph</field>
        <field name="keyword">graph algorithms</field>
        <field name="url">http://arxiv.org/abs/0704.0002</field>
      </doc>
      <doc>
        <!-- another document here -->
      </doc>
      <!-- and so on ... ->
    </add>

So each field has a name which matches the field names from the
`schema.xml`, the content of the tag is the value of the field.
Multi-valued fields can be repeated several times.

### Harvesting data from arXiv

To harvest data from arXiv you can use the `harvest-arxiv.py` script,
to see a list of options run:

    ./harvest-arxiv.py -h

At the moment it downloads only from the `cs` (Computer Science) set,
but you can change this and other details by editing the first lines
of the script.  To download everything, just run:

    mkdir output_dir
    ./harvest-arxiv.py -d output_dir

The script is a bit slow since arXiv mandates a short delay between
each fetch as not to overload the server. If later want to fetch
everything that has been updated since a particular date you can run
like this:

    mkdir output_dir_more
    ./harvest-arxiv.py -d output_dir_more -f 2015-08-31

Next you need to convert each file into a format understood by Solr:

    ./arxiv_to_solr.py output_dir*/*.xml

This will generate a huge `solr.xml` file. You can do this in smaller
steps as well so you don't have to create a huge file in one go. It
can be uploaded in pieces to the Solr database.

### Uploading to Solr

Finally upload your XML file to Solr. If you have used the harvesting
scripts from the previous section it will be the `solr.xml` file.

    /opt/solr/bin/post -c arxiv-cs solr.xml

You can safely upload the files many times, and upload again when new
files are available since they have a unique `id` and any new record
will overwrite the old one (i.e. you won't get duplicates).

Now you can head over to the web interface and make a query, just
select the database in the pull-down list on the left or go directly
to: <http://localhost:8983/solr/#/arxiv-cs/query>. Now type the query
in the `q` field and select the format of the result (e.g. json or
xml). Click "Execute query" when you are done, now you will see the
query result and the URL which you can use in your application, for
example:
<http://localhost:8983/solr/arxiv-cs/select?q=computer+vision&wt=json&indent=true>.

A useful option to add is `fl=*,score` which causes Solr to return the
relevance score of each result.

[1]: http://lucene.apache.org/solr/
[2]: https://wiki.apache.org/solr/SchemaXml
