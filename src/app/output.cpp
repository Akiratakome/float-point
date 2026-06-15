#include "app/output.hpp"

#include <filesystem>
#include <iomanip>
#include <sstream>

namespace hrsc::app {

std::string checkpoint_output_file(const std::string& output_file,
                                   std::size_t index) {
    std::filesystem::path path(output_file);
    std::ostringstream name;
    name << path.stem().string()
         << "_t" << std::setw(4) << std::setfill('0') << index
         << path.extension().string();
    std::filesystem::path out = path.has_parent_path()
        ? path.parent_path() / name.str()
        : std::filesystem::path(name.str());
    return out.string();
}

} // namespace hrsc::app
