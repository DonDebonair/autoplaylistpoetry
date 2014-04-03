Auto Playlist Poetry
====================

This little (web)app automatically generates [Spotify](https://www.spotify.com) playlists based on a search query entered by the user. _Auto Playlist Poetry_ is a proof-of-concept that's inspired by [**Playlist Poetry**](http://playlistpoetry.com/), which in turn was based on [this Tumbler blog](http://spotifypoetry.tumblr.com/). The idea is that the user can provide a message and the application will use the Spotify Metadata API to find songs whose titles together make up the provided message. 

Aside from the Flask app, there's also a simple commandline utility that does the same thing. 

## Disclaimer

A few caveats (ok, excuses really :) ) before trying out this app, and looking through the code:

* No Test-coverage whatsoever. You read that right. I know, it's a shame. I would have loved to provide tests for everything, but so far the time spent on this project was limited, and I consider this a proof-of-concept. Do know, that I am well aware of best practices in Software Engineering and that I normally go out of my way to provide decent test-coverage for the code I write. Tests are at the top of my TODO list for this project.
* External dependencies may make these applications fail sometimes. [The Spotify Metadata API](https://developer.spotify.com/technologies/web-api/) seems somewhat fickle, and will sometimes return either a undocumented HTTP 502 or 504 error. The odd thing is, that is seems to be related to the queries I feed it. Some queries always return a result, some queries often trigger a 502 or 504.
* Python is relatively new to me: In my current job I mainly develop in Java. I've done some Python programming as a hobby for some time now, and I really love the language! But I'm sure many of my solutions are "un-pythonic". I especially was unsure about how to organize my code, coming from an environment where everything is a class, and almost every class has it's own file. So I don't really know which code to put in what module/package/class/etc. Any ideas, contributions, PRs are welcome!

## The applications and installation/usage instructions

As said, there are two versions of the app: a command line app and a web app. Both (can) use Redis for caching the API results for later reuse. In the command line app, using Redis is optional, the web app requires it. You can install Redis using your favorite package manager, such as [homebrew](http://brew.sh/) on OS X. Aside from `redis`, two other external Python libraries are used: `requests` is used by both implementations for querying the Spotify Metadata API and `Flask` is used as a web framework in the web app.

To install the requirements, you can (assuming you have `pip` installed) do the following in your terminal: 

	pip install -r requirements.txt

If you only want to try out the command line app locally (which is easier), you could choose to only install `requests` and optionally `redis`.

### The command line app

The command line app has two different modes of operation: one-off or interactive. The latter can be invoked by passing `-i` or `--interactive` as an argument on the command line. Review the help by running:

	./cli.py --help
	
To run it for one message:

	./cli.py -m "if i can't let it go out of my mind"

The app tries to be a good unix-citizen and as such only gives back the endresult, without outputting any other messages during it's runtime. It also gives back 0 on success and non-0 on failure. Should you need more verbosity, you can pass `-v`. Without it, you only get the URIs for the playlist entries (or optionally the URLs)

The interactive mode let's you type in messages on a prompt, and returns the result. It's straigtforward enough. In iteractive mode, the app, by default, uses an in-memory caching mechanism for storing API results for later reuse. Both interactive and one-off mode can also use Redis by providing the `-r` switch, with optionally a hostname, port and password. It requires Redis to be running of course.

### The web app

The web application has a very simple interface which needs no further explanation. The application was built using [Flask](http://flask.pocoo.org/) and for the interface I used [Twitter Bootstrap](http://twitter.github.io/bootstrap/) (I know! just don't tell any designers…) The app uses Redis for caching API results for later reuse.

The web app also provides a very simple REST API. The endpoint resides at `/api/playlist` and requires a `message` to be passed in the query string. It gives back the result in JSON or returns an error in case something went wrong. It also tells you if the result is a complete playlist covering all the words, or if it's a partial result.

## Future improvements

Some future improvements could include:

* (unit)tests
* Dealing with skipping words to improve results
* Guarantee a maximum running time by setting time-outs for example. Strive for best-effort. Running time should improve however, when caching is used and the app is used many time, filling said cache.

## Contributions

...are very welcome!


