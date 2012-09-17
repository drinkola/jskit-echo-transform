This is a python script that will take a directory of XML files exported from JS-Kit, and transform them into a format suitable to submit to Echo2 via their api.
This was developed in Cygwin on Python v2.6 (hence the inclusion of argparse).
The script can either output the result XML to a file, or send to echo via their api (https://api.echoenabled.com/v1/submit). Modify the username and password values with your Echo Key and Secret. The API limits you to 100 entries per submission, so this script will break the entries into separate XML documents of that size. 

```
usage: Social Conversion [-h] [--s] [--file FILE] [--input_path INPUT_PATH]
                         [--output_path OUTPUT_PATH]

Convert JSKit Xml to Echo2 format

optional arguments:
  -h, --help				show this help message and exit
  --s						send to echo
  --file FILE				name of single file to process
  --input_path INPUT_PATH	location of files to process
  --output_path OUTPUT_PATH	write xml to this file
```