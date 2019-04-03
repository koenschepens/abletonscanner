
define([
    'utils/underscore',
], function(_) {

    return function(_api, _controller) {

        var modelGetters = [
            'buffer',
            'controls',
            'position',
            'duration',
            'fullscreen',
            'volume',
            'mute',
            'item', // this was playlistindex
            'stretching',
            'playlist'
        ];

        // given a name "buffer", it adds to jwplayer api a function named getBuffer
        _.each(modelGetters, function(attr) {
            var format = attr.slice(0,1).toUpperCase() + attr.slice(1);

            _api['get' + format] = function() {
                return _controller._model.get(attr);
            };
        });


        var passthroughs = [
            'getAudioTracks',
            'getCaptionsList',

            'getWidth',
            'getHeight',
            'getCurrentAudioTrack',
            'setCurrentAudioTrack',

            'getCurrentCaptions',
            'setCurrentCaptions',

            'getCurrentQuality',
            'setCurrentQuality',

            'getQualityLevels',
            'getVisualQuality',

            'getConfig',
            'getState',

            'getSafeRegion',
            'isBeforeComplete',
            'isBeforePlay',

            'getProvider',
            'detachMedia'

            // These are implemented in api.js, but should be here
            //'getItemMeta',
            //'getMeta',
            //'getPlaylistItem',
            //'getContainer',
            //'playlistItem',
        ];

        var passthroughsChain = [
            // Sisters of the model getters
            'setControls',
            'setFullscreen',
            'setVolume',
            'setMute',
            'setCues'
        ];

        // getters
        _.each(passthroughs, function(func) {
            _api[func] = function() {
                if (_controller[func]) {
                    return _controller[func].apply(_controller, arguments);
                }
                return null;
            };
        });
        // setters (chainable)
        _.each(passthroughsChain, function(func) {
            _api[func] = function() {
                _controller[func].apply(_controller, arguments);
                return _api;
            };
        });
    };
});
