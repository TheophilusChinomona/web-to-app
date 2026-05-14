const fs = require('fs');
const path = require('path');

module.exports = {
  documentDirectory: path.join(__dirname, '../tmp/'),

  async getInfoAsync(uri: string) {
    const exists = fs.existsSync(uri);
    return { exists, isFile: exists, isDirectory: false };
  },

  async readAsStringAsync(uri: string) {
    return fs.readFileSync(uri, 'utf8');
  },

  async writeAsStringAsync(uri: string, content: string) {
    fs.mkdirSync(path.dirname(uri), { recursive: true });
    fs.writeFileSync(uri, content, 'utf8');
  },

  async makeDirectoryAsync(uri: string) {
    fs.mkdirSync(uri, { recursive: true });
  },

  async readDirectoryAsync(uri: string) {
    return fs.readdirSync(uri);
  },
};
