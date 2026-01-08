// Pine Script v5 Syntax Highlighting for Highlight.js
// Mimics TradingView's syntax highlighting style

(function() {
    // Wait for hljs to be available
    if (typeof hljs === 'undefined') {
        console.error('Highlight.js not loaded');
        return;
    }
    
    // Define Pine Script language
    hljs.registerLanguage('pinescript', function(hljs) {
        // TradingView Pine Script keywords
        const KEYWORDS = 'if else for while switch break continue return export import var varip const';
        const LOGICAL_OPS = 'and or not';
        const LITERALS = 'true false na';
        const TYPES = 'int float bool string color line label box table array matrix map void simple series';
        
        // Built-in namespaces and common functions
        const BUILT_IN_FUNCTIONS = [
            'strategy', 'indicator', 'library', 'overlay', 'timestamp',
            'input', 'plot', 'plotshape', 'plotchar', 'plotarrow', 'plotcandle', 'plotbar',
            'hline', 'fill', 'bgcolor', 'barcolor',
            'line', 'label', 'box', 'table', 'alert', 'alertcondition',
            'close', 'open', 'high', 'low', 'volume', 'time', 'bar_index', 'hl2', 'hlc3', 'ohlc4',
            'ta', 'math', 'request', 'str', 'array', 'matrix', 'map', 'color',
            'timeframe', 'ticker', 'syminfo', 'barstate', 'session', 'dayofweek',
            'year', 'month', 'weekofyear', 'dayofmonth', 'dayofweek', 'hour', 'minute', 'second'
        ].join(' ');

        return {
            name: 'Pine Script',
            aliases: ['pine', 'pinescript'],
            case_insensitive: false,
            keywords: {
                keyword: KEYWORDS + ' ' + LOGICAL_OPS,
                literal: LITERALS,
                type: TYPES,
                built_in: BUILT_IN_FUNCTIONS
            },
            contains: [
                // Comments
                hljs.COMMENT('//', '$'),
                hljs.COMMENT('/\\*', '\\*/'),
                
                // Strings (TradingView orange color)
                {
                    className: 'string',
                    variants: [
                        hljs.QUOTE_STRING_MODE,
                        hljs.APOS_STRING_MODE
                    ]
                },
                
                // Numbers
                {
                    className: 'number',
                    variants: [
                        { begin: '\\b0[xX][0-9a-fA-F]+\\b' }, // Hex
                        { begin: '\\b\\d+(\\.\\d+)?([eE][+-]?\\d+)?\\b' } // Float/Int/Scientific
                    ]
                },
                
                // Built-in function calls with dot notation (strategy.entry, ta.sma, etc.)
                {
                    className: 'built_in',
                    begin: '\\b(strategy|ta|math|request|str|array|matrix|map|input|color|timeframe|ticker|syminfo|barstate|line|label|box|table)\\.',
                    end: '[a-zA-Z_][a-zA-Z0-9_]*',
                    returnEnd: true
                },
                
                // Type annotations
                {
                    className: 'type',
                    begin: '\\b(int|float|bool|string|color|line|label|box|table|array|matrix|map|void|simple|series)\\b'
                },
                
                // Assignment operator := (highlighted as keyword in Pine Script)
                {
                    className: 'operator',
                    begin: ':='
                }
            ]
        };
    });
    
    console.log('Pine Script syntax highlighting registered');
})();
