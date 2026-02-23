This is meant to be a simple viewer for some modern translations I'm making with another program.

The books will appear in `public/chapters` and their translations in `public/modern_chapters`.  The chapters are three digit text files, i.e. `000.txt` and `001.txt`, etc.  The `chapters` are the original text, while the `modern_chapters` have the same file names, but the files have two xml sections, on `<modernized_text>` section and one `<explanation>` section.  I'd like to display the modern translations, along with the original as well as the explanations in a simple interface that let's me move between books and chapters.


# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh
