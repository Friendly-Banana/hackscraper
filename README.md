# HackScraper

This tool automatically finds upcoming hackathons by checking websites where Hackathons are announced.  
HackScraper also normalizes the data for searching and filtering by location, time or theme.

A fully fledged permission system with suggested changes ensures published items have been reviewed by trusted users.

[![homepage of HackScraper, logo above 3 hackathon events with name and date](.github/homepage.png)](https://hack.gabriels.cloud/)

## Technical

Built with [Elixir](https://elixir-lang.org/) and [Phoenix](https://www.phoenixframework.org/), PostgreSQL as the database.

To start your Phoenix server:

  * Run `mix setup` to install and setup dependencies
  * Start Phoenix endpoint with `mix phx.server` or inside IEx with `iex -S mix phx.server`

Now you can visit [`localhost:4000`](http://localhost:4000) from your browser.


### Updating test snapshots


```sh
EXPOSURE_OVERRIDE=true mix test
```