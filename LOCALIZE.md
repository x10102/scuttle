# Localization

This file contains instructions for how to adapt SCUTTLE to your own wiki branch.

## Translation

SCUTTLE does not currently support i18n (though it is planned in the future), so you will have to translate strings directly inside the code.

To translate the app's UI, you will have to edit the Jinja templates in the `templates` folder. Other strings, such as flash messages, error messages and Discord webhook message templates, are located inside their respective `.py` files inside the `blueprints` and `connectors` folders.

## Discord login and configuration

Follow the instructions in `README.md`. You will have to register for a Discord developer account (free and very easy) and create an application on the [Discord Developer Portal](https://discord.com/developers/docs/intro). Don't forget to set up the redirect URIs to match the domain your instance will be accessed through.

## Setting your branch ID

Your wiki's language code should be entered into the `BRANCH_ID` variable inside `constants.py`

## Setting up your roles

SCUTTLE is built around the Czech branch's role system, and focuses primarily on translator roles, which are displayed on the front page. The equation used to calculate translator points per article is as follows:

`points = (words/1000)+bonus`

This is calculated directly inside the database using a somewhat complex view, which is not currently automatically created on first run (Peewee ORM's interface doesn't make it very straightforward). On first run, you will have to execute `scripts/create_db_original.sql` on your database, altering the calculation in the `Frontpage` view and inside `blueprints/articles.py` if needed.

After that is done, you can set up the point thresholds, names and colors of your roles in `framework/config/roles.yaml`.

The user marked as rolemaster will be notified through a webhook whenever a user's role changes, you can disable this by setting the `WEBHOOK_ENABLE` option to `false` in the configuration file, but note that this will also disable alerts for finished backups and granted/revoked administrator permissions.

## Editing user badges
Badges are small wikidot embeds designed to be placed in users' personal files on the wiki, showing their current role and some other statistics. For a usage example, check the personal files [on our wiki](http://scp-cs.wikidot.com/proc-to-nejde-dat-pryc).

New themes can be added as templates into the `templates/embeds/{translator,writer}` folder and set using a URL GET parameter when using the embed. After creating a new theme, you must run `scripts/build_badge_css.bat` to add the new Tailwind classes to the stylesheet. (The script is a Windows batch file, but only contains a single command that can be run in a linux shell) 

## Why the hell is this so complicated?
Modularity or future-proofing wasn't exactly on my mind while I was writing the first versions of SCUTTLE. If you need a hand setting SCUTTLE up for your branch, I'll be glad to help, just shoot me a message on Discord.
