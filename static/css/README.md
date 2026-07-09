# AlgoRadar CSS Architecture

This directory contains the modular CSS structure for AlgoRadar. The original monolithic `style.css` has been split into focused, maintainable modules.

## Directory Structure

```
static/css/
├── main.css           # Main entry point that imports all modules
├── base.css           # Reset, body, and fundamental styles
├── header.css         # Header and navigation components
├── forms.css          # Form elements and input styles
├── buttons.css        # Button styles and variants
├── tables.css         # Table layouts and styling
├── cards.css          # Card components
├── contact.css        # Contact page specific styles
├── admin.css          # Admin panel styles
├── utilities.css      # Utility classes
├── theme-dark.css     # Dark mode theme overrides
├── transitions.css    # Global transitions and animations
└── responsive.css     # Media queries and responsive design
```

## Module Descriptions

### Core Modules

- **main.css**: The main entry point that imports all CSS modules in the correct order. This is the only file that needs to be linked in HTML templates.

- **base.css**: Contains the CSS reset, body styles, and fundamental typography. Includes basic layout containers and footer styles.

- **header.css**: All header and navigation-related styles including the logo, nav menu, and theme toggle button.

### Component Modules

- **forms.css**: Comprehensive form styling including inputs, textareas, selects, labels, and form groups. Handles both standard forms and specialized form components.

- **buttons.css**: All button variants including primary, outline, submit, logout, and action buttons. Also includes button groups and action button containers.

- **tables.css**: Table styling for both basic and bordered tables. Includes hover effects, logos in tables, and special table states.

- **cards.css**: Card components including contest cards with platform-specific gradients and generic card layouts.

### Page-Specific Modules

- **contact.css**: Styles specific to the contact page including contact forms, direct contact links, FAQ sections, and social media icons.

- **admin.css**: Admin panel specific styles including the admin header and related components.

### Utility Modules

- **utilities.css**: Utility classes for spacing (margins, padding), width, display, alerts, badges, and text utilities.

- **theme-dark.css**: Complete dark mode theme implementation. Contains all style overrides for dark mode triggered by the `body.dark` class.

- **transitions.css**: Global transition and animation definitions for smooth UI interactions.

### Responsive Module

- **responsive.css**: Media queries for tablet (768px) and mobile (480px) breakpoints. Handles responsive behavior for all components.

## Usage

### In HTML Templates

Simply link to the main CSS file in your HTML templates:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
```

### Adding New Styles

When adding new styles:

1. Identify the appropriate module based on the style's purpose
2. Add styles to the relevant module file
3. If creating a new category, create a new module and import it in `main.css`
4. Maintain consistent ordering: base → layout → components → pages → utilities → themes → responsive

### Modifying Existing Styles

1. Use your browser's dev tools to identify which class you need to modify
2. Search for the class across all CSS files (or check the module based on the component type)
3. Make changes in the appropriate module file
4. Test in both light and dark modes
5. Verify responsive behavior

## Import Order

The import order in `main.css` is important:

1. **Base styles** first (reset and fundamentals)
2. **Layout components** (header, main structure)
3. **UI components** (forms, buttons, tables, cards)
4. **Page-specific styles**
5. **Utilities** (can override component styles)
6. **Theme overrides** (dark mode)
7. **Transitions** (global animations)
8. **Responsive styles** last (can override everything for specific breakpoints)

## Best Practices

1. **Keep modules focused**: Each module should have a single responsibility
2. **Avoid cross-dependencies**: Modules should be as independent as possible
3. **Use consistent naming**: Follow existing class naming conventions
4. **Document complex styles**: Add comments for non-obvious implementations
5. **Test dark mode**: Always verify styles work in both light and dark themes
6. **Check responsiveness**: Test on mobile, tablet, and desktop sizes

## Browser Support

The CSS is designed to work with modern browsers that support:
- CSS3 features (flexbox, grid, transitions)
- CSS custom properties (where used)
- Modern color functions

## Performance Notes

- CSS imports are handled at build/serve time by the browser
- All files are small and focused for better caching
- Minimal redundancy between modules
- Transitions are scoped to avoid performance issues

## Migration from Legacy

The original `style.css` file (1246 lines) has been split into 12 focused modules:
- Better maintainability
- Easier to find and modify styles
- Reduced merge conflicts in version control
- Improved code organization and readability

## Future Improvements

Potential enhancements for the CSS architecture:
- Add CSS preprocessor (SASS/LESS) for variables and mixins
- Implement CSS custom properties for theming
- Add print stylesheet
- Consider CSS-in-JS for component-specific styles
- Optimize with PostCSS for browser compatibility
