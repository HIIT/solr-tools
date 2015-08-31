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

## Create a new database in Solr

Let's create a new database named `arxiv-cs`. You have to run the
create command as the `solr` user like this:

    sudo -u solr /opt/solr/bin/solr create_core -c arxiv-cs -d data_driven_schema_configs

This creates a new core, which is the Solr term for a database. You
can have many cores in the same Solr instance. The `-c arxiv-cs`
option gives a name to the core, you can of course give it any name
you want. The `-d data_driven_schema_configs` option means that you do
not need to specify a schema for the database, but that it will derive
it automatically from the uploaded data.

A schema is a description of the fields and data types of each record
in the database, you can also specify the schema explicitly by
providing your own `schema.xml`. (This will be documented here
separately.)

## Fetch and import data to Solr

In this git repository are some example scripts to get data from arXiv
and convert them to Solr's format.

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

Finally upload this to Solr:

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
