#pragma once

#include <fstream>
#include <sstream>
#include <string>
#include <stdexcept>
#include <unordered_map>

namespace hrsc {

class Config {
    std::unordered_map<std::string, std::string> m_entries;

    static std::string trim(const std::string& s) {
        auto start = s.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) return "";
        auto end = s.find_last_not_of(" \t\r\n");
        return s.substr(start, end - start + 1);
    }

    void parse(std::istream& is) {
        std::string line;
        while (std::getline(is, line)) {
            std::string trimmed = trim(line);
            if (trimmed.empty() || trimmed[0] == '#') continue;

            auto eq_pos = trimmed.find('=');
            if (eq_pos == std::string::npos) continue;

            std::string key = trim(trimmed.substr(0, eq_pos));
            std::string val = trim(trimmed.substr(eq_pos + 1));
            if (!key.empty()) {
                m_entries[key] = val;
            }
        }
    }

public:
    explicit Config(std::istream& is) { parse(is); }

    explicit Config(const std::string& filename) {
        std::ifstream file(filename);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open config file: " + filename);
        }
        parse(file);
    }

    std::string get_string(const std::string& key,
                           const std::string& def = "") const {
        auto it = m_entries.find(key);
        return (it != m_entries.end()) ? it->second : def;
    }

    int get_int(const std::string& key, int def = 0) const {
        auto it = m_entries.find(key);
        if (it == m_entries.end()) return def;
        try {
            return std::stoi(it->second);
        } catch (const std::invalid_argument&) {
            throw std::runtime_error(
                "Failed to parse key '" + key + "' as int: " + it->second);
        } catch (const std::out_of_range&) {
            throw std::runtime_error(
                "Failed to parse key '" + key + "' as int (out of range): " + it->second);
        }
    }

    double get_double(const std::string& key, double def = 0.0) const {
        auto it = m_entries.find(key);
        if (it == m_entries.end()) return def;
        try {
            return std::stod(it->second);
        } catch (const std::invalid_argument&) {
            throw std::runtime_error(
                "Failed to parse key '" + key + "' as double: " + it->second);
        } catch (const std::out_of_range&) {
            throw std::runtime_error(
                "Failed to parse key '" + key + "' as double (out of range): " + it->second);
        }
    }

    bool get_bool(const std::string& key, bool def = false) const {
        auto it = m_entries.find(key);
        if (it == m_entries.end()) return def;
        const std::string& val = it->second;
        if (val == "true" || val == "1") return true;
        if (val == "false" || val == "0") return false;
        throw std::runtime_error(
            "Failed to parse key '" + key + "' as bool: " + val);
    }
};

} // namespace hrsc
