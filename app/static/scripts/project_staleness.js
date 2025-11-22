/**
 * Calculate project style based on staleness ratio
 * @param {number} staleness - Staleness ratio (0 = fresh, 1.0 = at threshold, >1.0 = overdue)
 * @returns {Object} Object with opacity and backgroundColor properties
 */
function calculateProjectStyle(staleness) {
    // Get CSS variables
    const styles = getComputedStyle(document.documentElement);
    const freshOpacity = parseFloat(styles.getPropertyValue('--project-fresh-opacity') || '1.0');
    const staleOpacity = parseFloat(styles.getPropertyValue('--project-stale-opacity') || '0.5');
    const stalenessStart = parseFloat(styles.getPropertyValue('--staleness-start') || '0.3');
    const stalenessMax = parseFloat(styles.getPropertyValue('--staleness-max') || '2.0');
    const bgColor = styles.getPropertyValue('--background-color').trim() || '#000000';

    // No fading if below threshold
    if (staleness < stalenessStart) {
        return {
            opacity: freshOpacity,
            backgroundColor: bgColor
        };
    }

    // Calculate fade factor (0 to 1)
    const fadeFactor = Math.min((staleness - stalenessStart) / (stalenessMax - stalenessStart), 1.0);
    
    // Calculate opacity (linear interpolation)
    const opacity = freshOpacity - (fadeFactor * (freshOpacity - staleOpacity));
    
    // Convert background color to rgba with reduced opacity
    const rgba = hexToRgba(bgColor, opacity);
    
    return {
        opacity: opacity,
        backgroundColor: rgba
    };
}

/**
 * Convert hex color to rgba with specified alpha
 * @param {string} hex - Hex color (e.g., '#000000')
 * @param {number} alpha - Alpha value (0-1)
 * @returns {string} RGBA color string
 */
function hexToRgba(hex, alpha) {
    hex = hex.replace('#', '');
    
    // Parse hex values
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Apply staleness styles to all project cards on page load
 */
function applyProjectStalenessStyles() {
    document.querySelectorAll('.project[data-staleness]').forEach(projectCard => {
        const staleness = parseFloat(projectCard.dataset.staleness);
        const style = calculateProjectStyle(staleness);
        
        projectCard.style.opacity = style.opacity;
        projectCard.style.backgroundColor = style.backgroundColor;
    });
}

// Apply styles when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyProjectStalenessStyles);
} else {
    applyProjectStalenessStyles();
}
