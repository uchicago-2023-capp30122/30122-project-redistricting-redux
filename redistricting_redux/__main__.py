from . import app #has to be this way for "python3 -m redistricting_redux" to run
#Do the poetry dependencies work right if you do it this way?

#import app # has to be this way for "poetry run python redistricting_redux" to run

#"from . import app" as in PA1 gives: "ImportError: attempted relative import with no known parent package"

#Do I need to have a separate app file a la PA1 or can it be all in here?
app.run()