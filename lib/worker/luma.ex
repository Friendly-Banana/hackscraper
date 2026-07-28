defmodule HackScraper.Worker.Luma do
  import HackScraper.Worker.Common
  require Logger

  def scrape(%{"url" => url} = args) do
    Logger.info("Running Luma scraper on #{url}...")

    events = get!(url).body["entries"]
    hackathons = filter_hackathons(events)
    Logger.info("Found #{length(hackathons)}/#{length(events)} hackathons")

    series_id = args["series_id"]

    jobs =
      hackathons
      |> Enum.with_index()
      |> Enum.map(fn {entry, index} ->
        event = entry["event"]

        %{
          "worker_name" => "Luma.AddInfo",
          "event" => %{
            "url" => URI.merge("https://luma.com", event["url"]) |> to_string(),
            "name" => event["name"],
            "start_date" => event["start_at"],
            "end_date" => event["end_at"],
            "series_id" => series_id
          }
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
      end)

    {:jobs, jobs}
  end

  defp filter_hackathons(entries) do
    Enum.filter(entries, fn entry ->
      event = entry["event"]
      name = String.downcase(event["name"] || "")
      String.contains?(name, ["hack", "coding", "tech challenge"])
    end)
  end
end

defmodule HackScraper.Worker.Luma.AddInfo do
  import HackScraper.Worker.Common
  require Logger

  def scrape(%{"event" => %{"url" => url} = event}) do
    Logger.info("Running Luma AddInfo scraper: #{url}...")

    html = get!(url).body |> Floki.parse_document!()

    json_ld =
      html
      |> Floki.find("script[type='application/ld+json']")
      |> List.first()
      |> case do
        {"script", _, [json_str]} -> Jason.decode!(json_str)
        _ -> %{}
      end

    description =
      case json_ld["description"] do
        desc when is_binary(desc) ->
          desc
          |> String.split("\n")
          |> Enum.take(5)
          |> Enum.join("\n")
          |> String.trim()

        _ ->
          ""
      end

    location =
      case json_ld["location"] do
        %{"name" => name} when is_binary(name) -> name
        _ -> nil
      end

    image =
      case json_ld["image"] do
        [first | _] when is_binary(first) -> first
        img when is_binary(img) -> img
        _ -> nil
      end

    hackathon =
      %{url: event["url"], name: event["name"], series_id: event["series_id"]}
      |> Map.put(:description, description)
      |> Map.put(:location, location)
      |> Map.put(:image, image)
      |> Map.put(:start_date, parse_date(event["start_date"] || json_ld["startDate"]))
      |> Map.put(:end_date, parse_date(event["end_date"] || json_ld["endDate"]))

    {:hackathons, [hackathon]}
  end
end
