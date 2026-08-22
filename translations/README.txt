Your plugin's translations will reside here. The provided Taskfile supports a
couple of additional commands to make managing your translations easier:

go-task babel-extract
    Extracts any translateable messages (marked with Jinja's `_("...")` or
    JavaScript's `gettext("...")`) and creates the initial `messages.pot` file.
go-task babel-refresh
    Reruns extraction and updates the `messages.pot` file.
go-task babel-new -- <locale>
    Creates a new translation folder for locale `<locale>`.
go-task babel-compile
    Compiles the translations into `mo` files, ready to be used within
    OctoPrint.

If you want to bundle translations with your plugin, create a new folder
`octoprint_octolapse/translations`. When that folder exists, an additional
command becomes available:

go-task babel-bundle
    Moves the translations for the locales defined in Taskfile.yml to
    octoprint_octolapse/translations, effectively bundling them with your
    plugin. This is interesting for languages you can guarantee to keep up to
    date yourself with each new release of your plugin.
