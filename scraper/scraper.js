// Import required modules
var jsdom = require('jsdom');
var request = require('request');
var fs = require('fs');
var path = require('path');

// Maximum number of pages to access
var MAX_SHOW_NUM = 20000;
// Maximum file name length, excluding extension
var FILENAME_LENGTH = 8;
// Where to save plot summaries
var PLOT_FOLDER = path.resolve('..', 'plot_summaries');

// `sprintf('%0Xd.txt', i)` where X = filename_length
function intToPaddedFilename(i, filename_length) {
	var iAsStr = i.toString();
	var numZeros = filename_length - iAsStr.length;
	return '0'.repeat(numZeros) + iAsStr + ".txt";
}

// Function that returns the request callback for a given url and id. This is needed so that
// URLs and requests don't get mixed up in a loop
function requestCb(url, id) {
	return function(err, response, body) {

		// Handle different request errors
		if(err) {
			console.error('Bad request for ' + url + ': Request error');
			console.error(err);
			return;
		}
		if(!response) {
			console.error('Bad request for ' + url + ': No response');
			return;
		}
		if(response.statusCode !== 200) {
			console.error('Bad request for ' + url + ': Bad status code ' + response.statusCode);
			return;
		}

		// Get DOM environment from the response body
		jsdom.env({
			html: body,
			scripts: ['http://code.jquery.com/jquery.js'],
			done: function(err, window) {
				if(err) {
					// Handle document error
					console.error('Failed to create DOM environment for ' + url);
					console.error(err);
					return;
				}

				// Get jQuery
				var $ = window.$;
				if(!$) {
					// Sometimes jQuery is not found randomly, so skip.
					// Usually it will be found on a second attempt...
					console.error('jQuery not found for ' + url + ', skipping');
					return;
				}

				// Get plot node
				var plotNode = $('span[itemprop="description"]')[0];
				if(!plotNode) {
					console.error('No plot found for ' + url);
					return;
				}

				// Extract plot from the node and write to file
				var plot = plotNode.textContent;
				var filePath = path.resolve(PLOT_FOLDER, intToPaddedFilename(id, FILENAME_LENGTH));
				fs.writeFile(filePath, plot, function(err) {
					if(err) {
						console.error('Failed to save plot for ' + url);
						console.error(err);
					}
					console.log('Saved plot for ' + url + ' to ' + filePath);
				});
			}
		});
	}
}

// Generic delayed loop function. Requires i to be initialized outside. The function has
// access to variable i
function delayedLoop(fn, maxI, delay) {
	setTimeout(function() {
		fn();
		if(++i < maxI) {
			delayedLoop(fn, maxI, delay);
		}
	}, delay);
}

var i = 1;
delayedLoop(function() {
	var url = 'https://myanimelist.net/anime/' + i.toString();
	request({uri: url}, requestCb(url, i));
}, MAX_SHOW_NUM+1, 500);
