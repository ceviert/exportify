#pragma once

#include <fstream>
#include <iostream>
#include <string>
#include <cstdlib>
#include <limits>
#include <nlohmann/json.hpp>
#include <vector>

struct IndexLinkPair {
  int index;
  std::string link;
};

class Menu {
  private:
    std::string json_path{"data/playlist_links.json"};
    std::vector<IndexLinkPair> playlist_links;
    bool terminate{false};
    int console_width_{60};
    std::string cache_songs_{"venv/bin/python3 ./cache_songs.py"};
    std::string download_songs_{"venv/bin/python3 download.py"};

    void removeLink();
    void downloadPlaylists();
    void cachePlaylists();
    void printLinks();
    void addNewLink();
    void parsePlaylistLinks();
    void saveToJson();
    void runCommand(const std::string& command);
    void waitForInput();
    void printMenu();
    void printCentered(const std::string& text, int width);
  public:
    void startMenu();
};