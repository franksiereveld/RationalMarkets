// Debug script - add console logging to key functions
(function() {
    console.log('=== DEBUG SCRIPT LOADED ===');
    
    // Intercept displayAnalysis
    const originalDisplayAnalysis = window.displayAnalysis;
    if (originalDisplayAnalysis) {
        window.displayAnalysis = function(analysis) {
            console.log('=== displayAnalysis called ===');
            console.log('Analysis:', analysis);
            console.log('Longs:', analysis.longs);
            console.log('Shorts:', analysis.shorts);
            return originalDisplayAnalysis.apply(this, arguments);
        };
    }
    
    // Intercept displayPositionsWithCharts
    const originalDisplayPositions = window.displayPositionsWithCharts;
    if (originalDisplayPositions) {
        window.displayPositionsWithCharts = function(positions, containerId, isLong) {
            console.log('=== displayPositionsWithCharts called ===');
            console.log(`Container: ${containerId}, isLong: ${isLong}`);
            console.log('Positions:', positions);
            if (positions && positions.length > 0) {
                console.log('First position:', positions[0]);
                console.log('  ticker:', positions[0].ticker);
                console.log('  currentPrice:', positions[0].currentPrice);
            }
            return originalDisplayPositions.apply(this, arguments);
        };
    }
    
    console.log('=== DEBUG SCRIPT READY ===');
})();

