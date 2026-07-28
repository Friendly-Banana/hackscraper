defmodule HackScraper.Worker.ScrapersTest do
  use ExUnit.Case, async: true
  import Exposure

  # List of scrapers to test.
  # The list includes the worker module, the target URL to mock,
  # and the input mock file path.
  @scrapers [
    %{
      name: "Devpost",
      module: HackScraper.Worker.Devpost,
      url:
        "https://devpost.com/api/hackathons?open_to[]=public&search=munich&status[]=upcoming&status[]=open",
      input: "test/worker/input/devpost.com.json"
    },
    %{
      name: "Huawei",
      module: HackScraper.Worker.Huawei,
      url: "https://huawei.agorize.com/api/v2/challenges",
      input: "test/worker/input/huawei.agorize.com.json"
    },
    %{
      name: "N3xtcoder",
      module: HackScraper.Worker.N3xtcoder,
      url: "https://n3xtcoder.org/api/event-cards?offset=0&sort=desc&pageSize=6&lang=en",
      input: "test/worker/input/n3xtcoder.org.json"
    },
    %{
      name: "Taikai",
      module: HackScraper.Worker.Taikai,
      url: "https://api.taikai.network/api/graphql",
      input: "test/worker/input/api.taikai.network.json"
    },
    %{
      name: "TUM Think Tank",
      module: HackScraper.Worker.TUMThinkTank,
      url: "https://tumthinktank.de/events/",
      input: "test/worker/input/tumthinktank.de.html"
    },
    %{
      name: "Unternehmertum",
      module: HackScraper.Worker.Unternehmertum,
      url: "https://www.unternehmertum.de/events?filter%5B%5D=9511",
      input: "test/worker/input/www.unternehmertum.de.html"
    },
    %{
      name: "Luma",
      module: HackScraper.Worker.Luma,
      url:
        "https://api2.luma.com/discover/get-paginated-events?latitude=48.13743&longitude=11.57549&pagination_limit=30&slug=tech",
      input: "test/worker/input/luma/luma.json"
    },
    %{
      name: "TUM Venture Labs",
      module: HackScraper.Worker.TUMVentureLabs,
      url:
        "https://www.tum-venture-labs.de/index.php?p=actions/sprig-core/components/render&eventFormats[]=66989&reset=false&search=&sprig:siteId=9a1761719fed643d2a9161f9bfa109521c7487343e041b2d3541f6f497b907ed1&sprig:id=18f5b0bbf1163c3ee576f32b2b84820f55e7f2099ee44df628295be00ca478d4s-events-list&sprig:component=7b3a1f07361ad5a76557bad89bff243735691e7103956a9201f2c2959b531556&sprig:template=49f84ea3b95926b92ef6f0545f1b9613962135886d4703c8e69d52dcaacc4088events/_event-list",
      input: "test/worker/input/tum venture labs/tum-venture-labs.html"
    },
    %{
      name: "LabLab",
      module: HackScraper.Worker.LabLab,
      url: "https://lablab.ai/ai-hackathons",
      input: "test/worker/input/lablab.ai.html"
    },
    %{
      name: "Direct HackTUM",
      module: HackScraper.Worker.Direct,
      url: "https://hack.tum.de",
      input: "test/worker/input/hack.tum.de.html"
    }
  ]

  # Dynamically generate a test for each primary scraper
  for scraper <- @scrapers do
    @scraper scraper

    test_snapshot "scrapes #{@scraper.name}" do
      module = @scraper.module
      url = @scraper.url
      input_path = @scraper.input

      # Load input data
      input_body = File.read!(input_path)

      input_data =
        if String.ends_with?(input_path, ".json") do
          Jason.decode!(input_body)
        else
          input_body
        end

      # Stub the shared Req.Test module to return the input data
      Req.Test.stub(HackScraper, fn conn ->
        if is_binary(input_data) do
          Req.Test.html(conn, input_data)
        else
          Req.Test.json(conn, input_data)
        end
      end)

      # Call the scraper's scrape/1 function directly
      {type, items} = module.scrape(%{"url" => url})

      # Normalize and sort the items for stable snapshot comparison
      normalized_items =
        items
        |> Enum.map(fn
          %Ecto.Changeset{} = changeset ->
            changeset.changes |> Map.delete(:scheduled_at)

          item ->
            item
        end)
        |> Enum.sort_by(fn item ->
          cond do
            is_map(item) and is_map(item[:args]) and is_map(item[:args]["event"]) ->
              item[:args]["event"]["url"]

            is_map(item) and is_map(item[:args]) ->
              item[:args]["url"]

            is_map(item) ->
              item[:url] || item["url"]

            true ->
              nil
          end
        end)

      # Return the normalized tuple for the snapshot assertion
      {type, normalized_items}
    end
  end

  @add_info_scrapers [
    %{
      name: "Luma AddInfo",
      parent_module: HackScraper.Worker.Luma,
      add_info_module: HackScraper.Worker.Luma.AddInfo,
      parent_url:
        "https://api2.luma.com/discover/get-paginated-events?latitude=48.13743&longitude=11.57549&pagination_limit=30&slug=tech",
      parent_input: "test/worker/input/luma/luma.json",
      folder: "test/worker/input/luma"
    },
    %{
      name: "TUM Venture Labs AddInfo",
      parent_module: HackScraper.Worker.TUMVentureLabs,
      add_info_module: HackScraper.Worker.TUMVentureLabs.AddInfo,
      parent_url:
        "https://www.tum-venture-labs.de/index.php?p=actions/sprig-core/components/render&eventFormats[]=66989&reset=false&search=&sprig:siteId=9a1761719fed643d2a9161f9bfa109521c7487343e041b2d3541f6f497b907ed1&sprig:id=18f5b0bbf1163c3ee576f32b2b84820f55e7f2099ee44df628295be00ca478d4s-events-list&sprig:component=7b3a1f07361ad5a76557bad89bff243735691e7103956a9201f2c2959b531556&sprig:template=49f84ea3b95926b92ef6f0545f1b9613962135886d4703c8e69d52dcaacc4088events/_event-list",
      parent_input: "test/worker/input/tum venture labs/tum-venture-labs.html",
      folder: "test/worker/input/tum venture labs"
    }
  ]

  # Dynamically generate a test for each AddInfo scraper across its input folder
  for add_info <- @add_info_scrapers do
    @add_info add_info

    test_snapshot "scrapes #{@add_info.name}" do
      parent_module = @add_info.parent_module
      add_info_module = @add_info.add_info_module
      parent_url = @add_info.parent_url
      parent_input_path = @add_info.parent_input
      folder = @add_info.folder

      # Load parent input data
      parent_body = File.read!(parent_input_path)

      parent_data =
        if String.ends_with?(parent_input_path, ".json") do
          Jason.decode!(parent_body)
        else
          parent_body
        end

      # Stub the shared Req.Test module to return the parent input data
      Req.Test.stub(HackScraper, fn conn ->
        if is_binary(parent_data) do
          Req.Test.html(conn, parent_data)
        else
          Req.Test.json(conn, parent_data)
        end
      end)

      # Call the parent scraper's scrape/1 function to get sub-jobs
      {:jobs, jobs} = parent_module.scrape(%{"url" => parent_url})

      # Run AddInfo scraper for each job whose HTML file exists in folder
      for job <- jobs do
        raw_args =
          case job do
            %Ecto.Changeset{changes: %{args: args}} -> args
            %{args: args} -> args
          end

        job_args = Jason.decode!(Jason.encode!(raw_args))

        event_url = job_args["event"]["url"]

        slug =
          event_url
          |> URI.parse()
          |> Map.get(:path)
          |> String.trim_trailing("/")
          |> Path.basename()

        file_path = Path.join(folder, "#{slug}.html")

        if File.exists?(file_path) do
          html_content = File.read!(file_path)

          Req.Test.stub(HackScraper, fn conn ->
            Req.Test.html(conn, html_content)
          end)

          add_info_module.scrape(job_args)
        else
          nil
        end
      end
    end
  end
end
