/** @type {import('tailwindcss').Config} */

module.exports = {
    content: [
        './h2h/templates/**/*.html',
        './h2h/static/**/*.js',
        './**/*.py',
    ],
    theme: {
        extend: {},
    },
    plugins: [require('daisyui')],
    safelist: [
        'alert-success',
        'alert-error',
        'alert-warning',
        'alert-info',
    ]
}
