<?php
   $query = $_GET["q"];
   if (!empty($query)) {
     $query_url = "http://kannonkoski.pc.hiit.fi:8888/solr/arxiv_cs/select?q=" .
       urlencode($query) . "&wt=json";
     $json = file_get_contents($query_url);
   }
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />  
    <title>Simple search</title>
  </head>
  <body>
    <h1>Simple search</h1>
    <p>Search the arXiv Computing Research Repository.<br />
       <a href="index.php.txt">View source code of this page</a>.</p>
    <form method="GET" action="index.php">
      <input type="text" name="q" value="<?php echo $query; ?>" />
      <input type="submit" value="Search" />      
    </form>
<?php
   if (!empty($json)) {
     $tree = json_decode($json);

     $header = $tree->{"responseHeader"};
     $time = $header->{"QTime"};

     $res = $tree->{"response"};
     $num_res = $res->{"numFound"};

     print("<p>Found $num_res results in $time ms using <a href=\"$query_url\">".
           "this query</a>. Here are the 10 first results.</p>");
     
     $docs = $res->{"docs"};
     foreach ($docs as $doc) { 
       $title = $doc->{"title"};
       $authors = $doc->{"author"};
       $url = $doc->{"url"};
       $abstract = $doc->{"abstract"};
       echo("<p><b><a href=\"$url\">$title</a></b><br />");
       echo(implode(", ", $authors) . ".</p>");
       echo("<quote>$abstract</quote>");
     }
   }
?>

  </body>
</html>


