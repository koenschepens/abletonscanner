define([
    'utils/underscore',
    'utils/helpers'
], function(_, utils) {

    var jwplayer = window.jwplayer;
    var storage = window.localStorage || {
            removeItem: utils.noop
        };

    function jwPrefix(str) {
        return 'jwplayer.' + str;
    }

    function getAllItems() {
        return _.reduce(this.persistItems, function(memo, key) {
            var val = storage[jwPrefix(key)];
            if (val) {
                memo[key] = utils.serialize(val);
            }
            return memo;
        }, {});
    }

    function setItem(name, value) {
        try {
            storage[jwPrefix(name)] = value;
        } catch(e) {
            // ignore QuotaExceededError unless debugging
            if (jwplayer && jwplayer.debug) {
                console.error(e);
            }
        }
    }

    function clear() {
        _.each(this.persistItems, function(val) {
            storage.removeItem(jwPrefix(val));
        });
    }

    function Storage() { }

    function track(persistItems, model) {
        this.persistItems = persistItems;

        _.each(this.persistItems, function(item) {
            model.on('change:' + item, function(model, value) {
                setItem(item, value);
            });
        });
    }

    _.extend(Storage.prototype, {
        getAllItems: getAllItems,
        track : track,
        clear: clear
    });

    return Storage;
});