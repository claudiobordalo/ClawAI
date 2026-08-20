"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.findFreePort = findFreePort;
const net_1 = __importDefault(require("net"));
/**
 * Find a free TCP port starting from the given port number.
 */
function findFreePort(startPort, maxAttempts = 100) {
    return new Promise((resolve, reject) => {
        const server = net_1.default.createServer();
        server.listen(startPort, '127.0.0.1', () => {
            const port = server.address().port;
            server.close(() => resolve(port));
        });
        server.on('error', () => {
            // Port is in use, try next
            findFreePort(startPort + 1, maxAttempts - 1)
                .then(resolve)
                .catch(reject);
        });
    });
}
