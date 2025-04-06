#include "Menu.hpp"

void Menu::printMenu() {
  std::cout << std::endl;
  printCentered("WELCOME TO EXPORTIFY®", console_width_);
  printCentered("==================================\n", console_width_);
  printCentered("1 - RUN SONG CACHER ", console_width_);
  printCentered("2 - RUN DOWNLOADER ", console_width_);
  printCentered("3 - SHOW SAVED LINKS", console_width_);
  printCentered("4 - ADD NEW LINK TO BE SAVED", console_width_);
  printCentered("5 - RUN AUTO DOWNLOADER", console_width_);
  printCentered("6 - RUN AUTO CACHER", console_width_);
  printCentered("7 - REMOVE LINK", console_width_);
  printCentered("X - ABOUT ", console_width_);
  printCentered("9 - EXIT ", console_width_);
}

void Menu::startMenu() {
  int choice;
  parsePlaylistLinks();
  while (!terminate) {
    printMenu();
    std::cout << ">";
    std::cin >> choice;

    if (std::cin.fail()) {
      std::cin.clear();
      std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
      std::cout << "Invalid input. Please enter a number.\n";
      continue;
    }

    switch (choice) {
      case 1:
        std::cout << "RUNNING SONG CACHER...\n";
        runCommand(cache_songs_);
        std::cout << "SONG CACHER EXITED!\n";
        break;
      case 2:
        std::cout << "RUNNING DOWNLOADER...\n";
        runCommand(download_songs_);
        std::cout << "DOWNLOADER EXITED!\n";
        break;
      case 3:
        printLinks();
        waitForInput();
        break;
      case 4:
        addNewLink();
        saveToJson();
        break;
      case 5:
        std::cout << "RUNNING AUTO DOWNLOADER WITH LINKS:\n";
        printLinks();
        downloadPlaylists();
        break;
      case 6:
        std::cout << "RUNNING AUTO CACHER WITH LINKS:\n";
        printLinks();
        cachePlaylists();
        break;
      case 7:
        std::cout << "RUNNING LINK REMOVER...\n";
        removeLink();
        saveToJson();
        break;
      case 8:
        break;
      case 9:
        std::cout << "EXITING EXPORTIFY!\n";
        terminate = true;
        break;
    }
  }
}

void Menu::printCentered(const std::string& text, int width) {
  int padding = (width - text.size()) / 2;
  if (padding > 0) {
    std::cout << std::string(padding, ' ') << text << std::endl;
  } else {
    std::cout << text << std::endl;
  }
}

void Menu::waitForInput() {
  std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
  std::cin.get();
}

void Menu::runCommand(const std::string& command) {
  std::string arg;
  std::cout << "[arg]>";
  std::cin >> arg;
  std::string result = command + " " + arg;
  system(result.c_str()); // convert it to const char *
}

void Menu::parsePlaylistLinks() {
  std::ifstream json_file(json_path);
  if (!json_file.is_open()) {
    std::cerr << "Failed to open json file: " << json_path << std::endl;
    return;
  }

  nlohmann::json json_data;
  json_file >> json_data;

  int i = 1;
  for (const auto& link : json_data) {
    playlist_links.push_back({i,link});
    i++;
  }
}

void Menu::saveToJson() {
  nlohmann::json json_data;

  for (const auto& element : playlist_links) {
    json_data.push_back(element.link);
  }

  std::ofstream json_file(json_path);
  if (!json_file.is_open()) {
    std::cerr << "Failed to open json file for writing: " << json_path << std::endl;
    return;
  }

  json_file << json_data.dump(4);
  json_file.close();

  std::cout << "Playlist links saved succesfully!" << std::endl;
}

void Menu::printLinks() {
  for (const auto& element : playlist_links) {
    std::cout << "-> " << "[" << element.index << "]" << element.link << std::endl;
  }
}

void Menu::addNewLink() {
  
  std::string input_link;
  std::cout << ">";
  std::cin >> input_link;
  for (const auto& element : playlist_links) {
    if (input_link == element.link) {
      std::cout << "Link already exists.\n" << std::endl;
      return;
    }
  }
  int size = playlist_links.size();
  playlist_links.push_back({size+1,input_link});
}

void Menu::downloadPlaylists() {
  for (const auto& element : playlist_links) {
    std::string full_comand = download_songs_ + " " + element.link;
    std::cout << "RUNNING DOWNLOADER WITH LINK: " << element.link << std::endl;
    system(full_comand.c_str());
  }
  std::cout << "AUTO DOWNLOADER EXITED!" << std::endl;
}

void Menu::cachePlaylists() {
  for (const auto& element : playlist_links) {
    std::string full_comand = cache_songs_ + " " + element.link;
    std::cout << "RUNNING CACHER WITH LINK: " << element.link << std::endl;
    system(full_comand.c_str());
  }
  std::cout << "AUTO CACHER EXITED!" << std::endl;
}

void Menu::removeLink() {
  printLinks();
  int index_choice;
  std::cout << "index of the link: ";
  std::cin >> index_choice;
  if (std::cin.fail()) {
    std::cin.clear();
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    std::cout << "Invalid input. Please enter a number.\n";
    return;
  }
  bool remove_success = false;
  for (auto& element : playlist_links) {
    if (index_choice == element.index && !remove_success) {
      playlist_links.erase(playlist_links.begin() + index_choice - 1);
      remove_success = true;
    }
    if (remove_success) {
      element.index--;
    }
  }
}