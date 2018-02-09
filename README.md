                  .        .           -     _
              .       .  ~   . ~  -  ~  . = .  ~
          ~        ~  __.---~~_~~_~~_~~_~ ~ ~~_~~~
        .    .     .-'  ` . ~_ = ~ _ =  . ~ .    ~
                 .'  `. ~  -   =      ~  -  _ ~ `
        ~    .  }` =  - _ ~  -  . ~  ` =  ~  _ . ~
              }`   . ~   =    ~  =  ~   -  ~    - _
    .        }   ~ .__,_O     ` ~ _   ~  ^  ~  -   
           `}` - =    /#/`-'     -   ~   =   ~  _ ~
      ~ .   }   ~ -   |^\   _ ~ _  - ~ -_  =  _  
           }`  _____ /_  /____ - ~ _   ~ _ 


Want to talk to the network of NOAA buoy's but don't want to parse the data. WAVE_THING is a gateway for you!

WAVE_THING acts as a HTTP gateway for translating the tabular data of the NOAA buoy API into JSON or XML. 

See it running [here](http://wavething.chalkfarm.org)

### WAVE_THING
WAVE_THING is a Python 3 application. To install Pyhton 3 if you don't already have it see [this guide](http://docs.python-guide.org/en/latest/starting/installation/) that covers the process for Linux, Mac OS X and Windows.

The access to WAVE_THING is through HTTP. It uses the [Flask](http://flask.pocoo.org/docs/0.12/) micro service to handle HTTP requests and responses. Installing Flask is taken care by the steps in the _To Run_ section of this document. It is pretty painless.

### To run:
```
pip install -r requirments.txt
python application.py
```

The gateway will now be accessible at http://127.0.0.1:5000/.

### To use:


To make a call against the NOAA data set the API path is 

```
/api/buoytalk/[buoy id]/[buoy data set]
```

The valid values for the `buoy data set` are defined on the [NOAA website](http://www.ndbc.noaa.gov/rt_data_access.shtml). 

_Note that not all buoys have all data sets available and WAVE_THING is not implementing all translations yet._

##### Command line example with CURL
```angular2html
curl -H "Accept: application/json"  http://127.0.0.1:5000/api/buoytalk/42001/spec
```

##### Programmatic example with Python 
```
import requests

# Which buoy and it's data I want
desired_buoy_id=42001
desired_buoy_data_set="txt"

# Make the request to the locally running instance of WAVE_THING
wave_thing_request = requests.get("http://127.0.0.1:5000/api/buoytalk/{buoy_id}/{buoy_data_set}".format(
    buoy_id=desired_buoy_id,
    buoy_data_set=desired_buoy_data_set
))

if wave_thing_request.status_code != 200:
    # Something went wrong
    print(wave_thing_request.text)
else:
    # Print the data!
    print(wave_thing_request.json())
```

Full documentation of the API in SWAGGER format is in the file wave_thing.swagger.yaml. 

### Internet accessible WAVE_THING with AWS:

WAVE_THING will also run fine on AWS ElasticBeanStalk. Follow the steps on the AWS [documentation page](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html) to deploy on ElasticBeanstalk.