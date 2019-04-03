define([
    'api/config',
    'api/api-deprecate',
    'controller/instream-adapter',
    'utils/underscore',
    'controller/Setup',
    'controller/captions',
    'controller/model',
    'playlist/playlist',
    'playlist/loader',
    'utils/helpers',
    'view/view',
    'utils/backbone.events',
    'events/change-state-event',
    'events/states',
    'events/events',
    'view/error'
], function(Config, deprecateInit, InstreamAdapter, _, Setup, Captions,
            Model, Playlist, PlaylistLoader, utils, View, Events, changeStateEvent, states, events, error) {

    function _queue(command) {
        return function() {
            var args = Array.prototype.slice.call(arguments, 0);
            this.eventsQueue.push([command, args]);
        };
    }

    // The model stores a different state than the provider
    function normalizeState(newstate) {
        if (newstate === states.LOADING || newstate === states.STALLED) {
            return states.BUFFERING;
        }
        return newstate;
    }

    var Controller = function(originalContainer) {
        this.originalContainer = this.currentContainer = originalContainer;
        this.eventsQueue = [];
        _.extend(this, Events);

        this._model = new Model();
    };

    Controller.prototype = {
        play : _queue('play'),
        pause : _queue('pause'),
        setVolume : _queue('setVolume'),
        setMute : _queue('setMute'),
        seek : _queue('seek'),
        stop : _queue('stop'),
        load : _queue('load'),
        playlistNext : _queue('playlistNext'),
        playlistPrev : _queue('playlistPrev'),
        playlistItem : _queue('playlistItem'),
        setFullscreen : _queue('setFullscreen'),
        setCurrentCaptions : _queue('setCurrentCaptions'),
        setCurrentQuality : _queue('setCurrentQuality'),

        setup : function(options, _api) {

            var _model,
                _view,
                _captions,
                _setup,
                _preplay = false,
                _actionOnAttach,
                _stopPlaylist = false, // onComplete, should we play next item or not?
                _interruptPlay,
                _this = this;

            var _video = function() { return _model.getVideo(); };

            var config = new Config(options);

            _model = this._model.setup(config);
            _view  = this._view  = new View(_api, _model);
            _captions = new Captions(_api, _model);
            _setup = new Setup(_api, _model, _view, _setPlaylist);

            _setup.on(events.JWPLAYER_READY, _playerReady, this);
            _setup.on(events.JWPLAYER_SETUP_ERROR, this.setupError, this);

            _model.mediaController.on(events.JWPLAYER_MEDIA_COMPLETE, function() {
                // Insert a small delay here so that other complete handlers can execute
                _.defer(_completeHandler);
            });
            _model.mediaController.on(events.JWPLAYER_MEDIA_ERROR, this.triggerError, this);

            // If we attempt to load flash, assume it is blocked if we don't hear back within a second
            _model.on('change:flashBlocked', function(model, isBlocked) {
                if (isBlocked) {
                    this.trigger(events.JWPLAYER_ERROR, {
                        message: 'Flash plugin is blocked'
                    });
                }
            }, this);

            function initMediaModel() {
                _model.mediaModel.on('change:state', function(mediaModel, state) {
                    var modelState = normalizeState(state);
                    _model.set('state', modelState);
                });
            }
            initMediaModel();
            _model.on('change:mediaModel', initMediaModel);

            function _playerReady() {
                _setup = null;

                // Set up provider and allow preload
                _setItem(_model.get('item'));

                _model.on('change:state', changeStateEvent, this);

                // For 'onCast' callback
                _model.on('change:castState', function(model, evt) {
                    _this.trigger(events.JWPLAYER_CAST_SESSION, evt);
                });
                // For 'onFullscreen' callback
                _model.on('change:fullscreen', function(model, bool) {
                    _this.trigger(events.JWPLAYER_FULLSCREEN, {
                        fullscreen: bool
                    });
                });
                // For onItem callback
                _model.on('itemReady', function() {
                    _this.trigger(events.JWPLAYER_PLAYLIST_ITEM, {
                        index: _model.get('item'),
                        item: _model.get('playlistItem')
                    });
                });
                // For onPlaylist callback
                _model.on('change:playlist', function(model, playlist) {
                    if (playlist.length) {
                        _this.trigger(events.JWPLAYER_PLAYLIST_LOADED, {
                            playlist: playlist
                        });
                    }
                });
                _model.on('change:volume', function(model, vol) {
                    _this.trigger(events.JWPLAYER_MEDIA_VOLUME, {
                        volume: vol
                    });
                });
                _model.on('change:mute', function(model, mute) {
                    _this.trigger(events.JWPLAYER_MEDIA_MUTE, {
                        mute: mute
                    });
                });
                _model.on('change:controls', function(model, mode) {
                    _this.trigger(events.JWPLAYER_CONTROLS, {
                        controls: mode
                    });
                });

                _model.on('change:scrubbing', function(model, state) {
                    if (state) {
                        _pause();
                    } else {
                        _play();
                    }
                });

                // For onCaptionsList and onCaptionsChange
                _model.on('change:captionsList', function(model, captionsList) {
                    _this.trigger(events.JWPLAYER_CAPTIONS_LIST, {
                        tracks: captionsList,
                        track: _getCurrentCaptions()
                    });
                });

                _model.mediaController.on('all', _this.trigger.bind(_this));
                _view.on('all', _this.trigger.bind(_this));

                this.showView(_view.element());

                // prevent video error in display on window close
                window.addEventListener('beforeunload', function() {
                    if (!_isCasting()) { // don't call stop while casting
                        _stop(true);
                    }
                });

                // Defer triggering of events until they can be registered
                _.defer(_playerReadyNotify);
            }

            function _playerReadyNotify() {
                // Tell the api that we are loaded
                _this.trigger(events.JWPLAYER_READY, {
                    // this will be updated by Api
                    setupTime: 0
                });

                _this.trigger(events.JWPLAYER_PLAYLIST_LOADED, {
                    playlist: _model.get('playlist')
                });
                _this.trigger(events.JWPLAYER_PLAYLIST_ITEM, {
                    index: _model.get('item'),
                    item: _model.get('playlistItem')
                });
                
                _this.trigger(events.JWPLAYER_CAPTIONS_LIST, {
                    tracks: _model.get('captionsList'),
                    track: _model.get('captionsIndex')
                });

                if (_model.get('autostart')) {
                    _play();
                }

                while (_this.eventsQueue.length > 0) {
                    var q = _this.eventsQueue.shift();
                    var method = q[0];
                    var args = q[1] || [];
                    _this[method].apply(_this, args);
                }
            }

            function _load(item) {
                if (_model.get('state') === states.ERROR) {
                    _model.set('state', states.IDLE);
                }
                _stop(true);

                if (_model.get('autostart')) {
                    _model.once('itemReady', _play);
                }

                switch (typeof item) {
                    case 'string':
                        _loadPlaylist(item);
                        break;
                    case 'object':
                        _setPlaylist(item);
                        _setItem(0);
                        break;
                    case 'number':
                        _setItem(item);
                        break;
                }
            }

            function _loadPlaylist(toLoad) {
                var loader = new PlaylistLoader();
                loader.on(events.JWPLAYER_PLAYLIST_LOADED, function(evt) {
                    _load(evt.playlist);
                });
                loader.on(events.JWPLAYER_ERROR, function(evt) {
                    evt.message = 'Error loading playlist: ' + evt.message;
                    this.triggerError(evt);
                }, this);
                loader.load(toLoad);
            }

            function _getState() {
                var adState = _this._instreamAdapter && _this._instreamAdapter.getState();
                if (_.isString(adState)) {
                    return adState;
                }
                return _model.get('state');
            }

            function _play() {
                var status;

                if(_model.get('state') === states.ERROR) {
                    return;
                }

                var adState = _this._instreamAdapter && _this._instreamAdapter.getState();
                if (_.isString(adState)) {
                    // this will resume the ad. _api.playAd would load a new ad
                    return _api.pauseAd(false);
                }

                if (_model.get('state') === states.COMPLETE) {
                    _stop(true);
                    _setItem(0);
                }
                if (!_preplay) {
                    _preplay = true;
                    _this.trigger(events.JWPLAYER_MEDIA_BEFOREPLAY, {});
                    _preplay = false;
                    if (_interruptPlay) {
                        _interruptPlay = false;
                        _actionOnAttach = null;
                        return;
                    }
                }

                if (_isIdle()) {
                    if (_model.get('playlist').length === 0) {
                        return false;
                    }

                    status = utils.tryCatch(function() {
                        _model.loadVideo();
                    });
                } else if (_model.get('state') === states.PAUSED) {
                    status = utils.tryCatch(function() {
                        _model.playVideo();
                    });
                }

                if (status instanceof utils.Error) {
                    _this.triggerError(status);
                    _actionOnAttach = null;
                    return false;
                }
                return true;
            }

            function _stop(internal) {
                // Reset the autostart play
                _model.off('itemReady', _play);

                var fromApi = !internal;

                _actionOnAttach = null;

                var status = utils.tryCatch(function() {
                    _model.stopVideo();
                }, _this);

                if (status instanceof utils.Error) {
                    _this.triggerError(status);
                    return false;
                }

                if (fromApi) {
                    _stopPlaylist = true;
                }

                if (_preplay) {
                    _interruptPlay = true;
                }

                return true;
            }

            function _pause() {
                _actionOnAttach = null;

                var adState = _this._instreamAdapter && _this._instreamAdapter.getState();
                if (_.isString(adState)) {
                    return _api.pauseAd(true);
                }

                switch (_model.get('state')) {
                    case states.ERROR:
                        return false;
                    case states.PLAYING:
                    case states.BUFFERING:
                        var status = utils.tryCatch(function(){
                            _video().pause();
                        }, this);

                        if (status instanceof utils.Error) {
                            _this.triggerError(status);
                            return false;
                        }
                        break;
                    default:
                        if (_preplay) {
                            _interruptPlay = true;
                        }
                }
                return true;
            }

            function _isIdle() {
                var state = _model.get('state');
                return (state === states.IDLE || state === states.COMPLETE || state === states.ERROR);
            }

            function _seek(pos) {
                if(_model.get('state') === states.ERROR) {
                    return;
                }
                if (!_model.get('scrubbing') && _model.get('state') !== states.PLAYING) {
                    _play(true);
                }
                _video().seek(pos);
            }

            function _item(index) {
                _stop(true);
                _setItem(index);
                _play();
            }

            function _setPlaylist(p) {
                var playlist = Playlist(p);
                playlist = Playlist.filterPlaylist(playlist, _model.getProviders(), _model.get('androidhls'),
                    _model.get('drm'), _model.get('preload'));

                _model.set('playlist', playlist);

                if (playlist.length === 0) {
                    _model.mediaController.trigger(events.JWPLAYER_ERROR, {
                        message: 'Error loading playlist: No playable sources found'
                    });
                    return;
                }
            }

            function _setItem(index) {
                var playlist = _model.get('playlist');

                // If looping past the end, or before the beginning
                index = (index + playlist.length) % playlist.length;

                _model.set('item', index);
                _model.set('playlistItem', playlist[index]);
                _model.setActiveItem(playlist[index]);
            }

            function _prev() {
                _item(_model.get('item') - 1);
            }

            function _next() {
                _item(_model.get('item') + 1);
            }

            function _completeHandler() {
                if (!_isIdle()) {
                    // Something has made an API call before the complete handler has fired.
                    return;
                } else if (_stopPlaylist) {
                    // Stop called in onComplete event listener
                    _stopPlaylist = false;
                    return;
                }

                _actionOnAttach = _completeHandler;

                var idx = _model.get('item');
                if (idx === _model.get('playlist').length - 1) {
                    // If it's the last item in the playlist
                    if (_model.get('repeat')) {
                        _next();
                    } else {
                        _model.set('state', states.COMPLETE);
                        _this.trigger(events.JWPLAYER_PLAYLIST_COMPLETE, {});
                    }
                    return;
                }

                // It wasn't the last item in the playlist,
                //  so go to the next one
                _next();
            }

            function _setCurrentQuality(quality) {
                _video().setCurrentQuality(quality);
            }

            function _getCurrentQuality() {
                if (_video()) {
                    return _video().getCurrentQuality();
                }
                return -1;
            }

            function _getConfig() {
                if (this._model) {
                    return this._model.getConfiguration();
                }
            }

            function _getVisualQuality() {
                if (this._model.mediaModel) {
                    return this._model.mediaModel.get('visualQuality');
                }
                // if quality is not implemented in the provider,
                // return quality info based on current level
                var qualityLevels = _getQualityLevels();
                if (qualityLevels) {
                    var levelIndex = _getCurrentQuality();
                    var level = qualityLevels[levelIndex];
                    if (level) {
                        return {
                            level: _.extend({
                                index: levelIndex
                            }, level),
                            mode: '',
                            reason: ''
                        };
                    }
                }
                return null;
            }

            function _getQualityLevels() {
                if (_video()) {
                    return _video().getQualityLevels();
                }
                return null;
            }

            function _setCurrentAudioTrack(index) {
                _video().setCurrentAudioTrack(index);
            }

            function _getCurrentAudioTrack() {
                if (_video()) {
                    return _video().getCurrentAudioTrack();
                }
                return -1;
            }

            function _getAudioTracks() {
                if (_video()) {
                    return _video().getAudioTracks();
                }
                return null;
            }

            function _setCurrentCaptions(index) {
                // update provider subtitle track
                _model.setVideoSubtitleTrack(index);

                _this.trigger(events.JWPLAYER_CAPTIONS_CHANGED, {
                    tracks: _getCaptionsList(),
                    track: index
                });

            }

            function _getCurrentCaptions() {
                return _captions.getCurrentIndex();
            }

            function _getCaptionsList() {
                return _captions.getCaptionsList();
            }

            /** Used for the InStream API **/
            function _detachMedia() {
                var provider = _model.getVideo();
                if (provider) {
                    var video = provider.detachMedia();
                    if (video instanceof HTMLVideoElement) {
                        return video;
                    }
                }
                return null;
            }

            function _isCasting() {
                var provider = _model.getVideo();
                if (provider) {
                    return provider.isCaster;
                }
                return false;
            }

            function _attachMedia(seekable) {
                // Called after instream ends
                var status = utils.tryCatch(function() {
                    _model.getVideo().attachMedia(seekable);
                });

                if (status instanceof utils.Error) {
                    utils.log('Error calling _attachMedia', status);
                    return;
                }

                if (typeof _actionOnAttach === 'function') {
                    _actionOnAttach();
                }
            }

            /** Controller API / public methods **/
            this.play = _play;
            this.pause = _pause;
            this.seek = _seek;
            this.stop = _stop;
            this.load = _load;
            this.playlistNext = _next;
            this.playlistPrev = _prev;
            this.playlistItem = _item;
            this.setCurrentCaptions = _setCurrentCaptions;
            this.setCurrentQuality = _setCurrentQuality;

            this.detachMedia = _detachMedia;
            this.attachMedia = _attachMedia;
            this.getCurrentQuality = _getCurrentQuality;
            this.getQualityLevels = _getQualityLevels;
            this.setCurrentAudioTrack = _setCurrentAudioTrack;
            this.getCurrentAudioTrack = _getCurrentAudioTrack;
            this.getAudioTracks = _getAudioTracks;
            this.getCurrentCaptions = _getCurrentCaptions;
            this.getCaptionsList = _getCaptionsList;
            this.getVisualQuality = _getVisualQuality;
            this.getConfig = _getConfig;
            this.getState = _getState;

            // Model passthroughs
            this.setVolume = _model.setVolume;
            this.setMute = _model.setMute;
            this.getProvider = function(){ return _model.get('provider'); };
            this.getWidth = function() { return _model.get('containerWidth'); };
            this.getHeight = function() { return _model.get('containerHeight'); };

            // View passthroughs
            this.getContainer = function(){ return this.currentContainer; };
            this.resize = _view.resize;
            this.getSafeRegion = _view.getSafeRegion;
            //this.forceState = _view.forceState;
            //this.releaseState = _view.releaseState;
            this.setCues = _view.addCues;

            this.setFullscreen = function(state) {
                if (!_.isBoolean(state)) {
                    state = !_model.get('fullscreen');
                }

                _model.set('fullscreen', state);
                if (this._instreamAdapter) {
                    this._instreamAdapter._adModel.set('fullscreen', state);
                }
            };

            this.addButton = function(img, tooltip, callback, id, btnClass) {
                var btn = {
                    img : img,
                    tooltip : tooltip,
                    callback : callback,
                    id : id,
                    class : btnClass
                };

                var dock = _model.get('dock');
                dock = (dock) ? dock.slice(0) : [];
                dock = _.reject(dock, _.matches({id : btn.id}));

                dock.push(btn);
                _model.set('dock', dock);
            };

            this.removeButton = function(id) {
                var dock = _model.get('dock') || [];
                dock = _.reject(dock, _.matches({id : id}));
                _model.set('dock', dock);
            };

            this.checkBeforePlay = function() {
                return _preplay;
            };

            this.getItemQoe = function() {
                return _model._qoeItem;
            };

            this.setControls = function (mode) {
                if (!_.isBoolean(mode)) {
                    mode = ! _model.get('controls');
                }
                _model.set('controls', mode);

                var provider = _model.getVideo();
                if (provider) {
                    provider.setControls(mode);
                }
            };

            this.playerDestroy = function () {
                this.stop();

                this.showView(this.originalContainer);

                if (_view) {
                    _view.destroy();
                }
                if (_model) {
                    _model.destroy();
                }
                if (_setup) {
                    _setup.destroy();
                    _setup = null;
                }
            };

            this.isBeforePlay = this.checkBeforePlay;

            this.isBeforeComplete = function () {
                return _model.getVideo().checkComplete();
            };

            this.createInstream = function() {
                this.instreamDestroy();
                this._instreamAdapter = new InstreamAdapter(this, _model, _view);
                return this._instreamAdapter;
            };

            this.skipAd = function() {
                if (this._instreamAdapter) {
                    this._instreamAdapter.skipAd();
                }
            };

            this.instreamDestroy = function() {
                if (_this._instreamAdapter) {
                    _this._instreamAdapter.destroy();
                }
            };

            // This is here because it binds to the methods declared above
            deprecateInit(_api, this);

            _setup.start();
        },

        showView: function(viewElement){
            if (!document.documentElement.contains(this.currentContainer)) {
                // This implies the player was removed from the DOM before setup completed
                //   or a player has been "re" setup after being removed from the DOM
                this.currentContainer = document.getElementById(this._model.get('id'));
                if (!this.currentContainer) {
                    return;
                }
            }

            if(this.currentContainer.parentElement) {
                this.currentContainer.parentElement.replaceChild(viewElement, this.currentContainer);
            }
            this.currentContainer = viewElement;
        },

        triggerError: function(evt) {

            this._model.set('errorEvent', evt);
            this._model.set('state', states.ERROR);
            this._model.once('change:state', function() {
                this._model.set('errorEvent', undefined);
            }, this);

            this.trigger(events.JWPLAYER_ERROR, evt);
        },

        setupError: function(evt){
            var message = evt.message;
            var errorElement = utils.createElement(error(this._model.get('id'), this._model.get('skin'), message));

            var width = this._model.get('width'),
                height = this._model.get('height');

            utils.style(errorElement, {
                width: width.toString().indexOf('%') > 0 ? width : (width+ 'px'),
                height: height.toString().indexOf('%') > 0 ? height : (height + 'px')
            });

            this.showView(errorElement);

            var _this = this;
            _.defer(function() {
                _this.trigger(events.JWPLAYER_SETUP_ERROR, {
                    message: message
                });
            });
        }
    };

    return Controller;
});

