defmodule HackScraper.Worker.TUMVentureLabs do
  import HackScraper.Worker.Common
  require Logger

  def scrape(%{"url" => url} = args) do
    Logger.info("Running TUMVentureLabs scraper...")

    html = get!(url).body
    cards = html |> Floki.parse_document!() |> Floki.find(".grid .sm\\:col-6")
    Logger.info("Found #{length(cards)} events")

    series_id = args["series_id"]

    jobs =
      for {card, index} <- Enum.with_index(cards) do
        link = Floki.find(card, "a")
        url = Floki.attribute(link, "href") |> List.first()
        name = Floki.text(link) |> String.trim()

        date =
          card
          |> Floki.find("p.fw-bold")
          |> Floki.text()
          |> String.trim()

        event = %{url: url, name: name, date_hint: date, series_id: series_id}

        %{
          "worker_name" => "TUMVentureLabs.AddInfo",
          "event" => event
        }
        |> HackScraper.Worker.ScraperRunner.new(
          schedule_in: index * 180,
          priority: 3,
          max_attempts: 2,
          unique: [
            period: {60, :days},
            states: :all,
            fields: [:queue, :args],
            keys: [:event]
          ]
        )
      end

    Logger.info("Queued AddInfo jobs")
    {:jobs, jobs}
  end
end

defmodule HackScraper.Worker.TUMVentureLabs.AddInfo do
  import HackScraper.Worker.Common
  require Logger

  def scrape(%{"event" => %{"url" => url} = event}) do
    Logger.info("Running TUMVentureLabs AddInfo scraper: #{url}...")

    html = get!(url).body |> Floki.parse_document!()

    description =
      html
      |> Floki.find("div.prose")
      |> List.first()
      |> Floki.text(sep: "\n")
      |> String.trim()

    location =
      html
      |> Floki.find(".facts-dl-item")
      |> Enum.find_value(fn item ->
        term = Floki.find(item, ".facts-dl-term") |> Floki.text() |> String.trim()

        if term == "Where" do
          Floki.find(item, ".facts-dl-definition") |> Floki.text() |> String.trim()
        end
      end)

    actual_url =
      html
      |> Floki.find(".header-split-content-footer a")
      |> Floki.attribute("href")
      |> List.first()

    event_atoms =
      for {key, val} <- event,
          into: %{},
          do: {String.to_existing_atom(key), val}

    map =
      event_atoms
      |> Map.put(:description, description)
      |> Map.put(:location, location)
      |> Map.put(:image, extract_best_image(html))

    suggestion = if actual_url, do: Map.put(map, :url, actual_url), else: map

    {:suggestions, [suggestion]}
  end

  defp extract_best_image(html) do
    img = Floki.find(html, ".header-split-image img")

    with [srcset | _] <- Floki.attribute(img, "srcset"),
         parsed when parsed != [] <- parse_srcset(srcset) do
      parsed |> Enum.max_by(&elem(&1, 0)) |> elem(1)
    else
      _ -> img |> Floki.attribute("src") |> List.first()
    end
  end

  defp parse_srcset(srcset) do
    srcset
    |> String.split(",")
    |> Enum.flat_map(fn entry ->
      case String.split(entry, ~r/\s+/, trim: true) do
        [url | rest] ->
          width =
            case rest do
              [desc | _] ->
                case Integer.parse(desc) do
                  {w, _} -> w
                  _ -> 0
                end

              _ -> 0
            end

          [{width, url}]

        [] ->
          []
      end
    end)
  end
end
