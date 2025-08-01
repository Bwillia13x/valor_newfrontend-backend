class VersionControl {
    constructor() {
        this.versionHistory = new Map();
        this.currentVersion = 0;
        this.currentUser = null;
    }
    
    setCurrentUser(user) {
        this.currentUser = user;
    }
    
    createSnapshot(document) {
        const snapshot = {
            version: this.currentVersion++,
            timestamp: Date.now(),
            data: this.deepClone(document),
            author: this.currentUser
        };
        this.versionHistory.set(snapshot.version, snapshot);
        return snapshot;
    }
    
    deepClone(obj) {
        // Handle complex objects with circular references
        return JSON.parse(JSON.stringify(obj));
    }
    
    getSnapshotByVersion(version) {
        return this.versionHistory.get(version) || null;
    }
    
    compareVersions(version1, version2) {
        const v1 = this.versionHistory.get(version1);
        const v2 = this.versionHistory.get(version2);
        return {
            differences: this.diffDocuments(v1.data, v2.data),
            version1: v1.version,
            version2: v2.version
        };
    }
    
    diffDocuments(doc1, doc2) {
        // Basic text diff implementation
        const diff = [];
        const maxLength = Math.max(doc1.length, doc2.length);
        
        for (let i = 0; i < maxLength; i++) {
            if (doc1[i] !== doc2[i]) {
                diff.push({
                    position: i,
                    from: doc1[i] || null,
                    to: doc2[i] || null
                });
            }
        }
        
        return diff;
    }
}
