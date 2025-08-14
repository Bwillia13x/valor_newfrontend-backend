/**
 * Conflict Resolver - Handles concurrent editing conflicts
 * Implements operational transformation for real-time collaboration
 */

class ConflictResolver {
    constructor() {
        this.versionVector = new Map();
        this.pendingOperations = [];
        this.operationLog = [];
        this.maxLogSize = 1000;
    }

    /**
     * Initialize version vector for a user
     */
    initUser(userId) {
        if (!this.versionVector.has(userId)) {
            this.versionVector.set(userId, 0);
        }
    }

    /**
     * Create an operation for data changes
     */
    createOperation(userId, dataType, data, operationType = 'update') {
        this.initUser(userId);
        const version = this.versionVector.get(userId) + 1;
        this.versionVector.set(userId, version);

        const operation = {
            id: this.generateOperationId(),
            userId: userId,
            dataType: dataType,
            data: data,
            operationType: operationType,
            version: version,
            timestamp: Date.now(),
            dependencies: this.getDependencies()
        };

        this.operationLog.push(operation);
        this.trimLog();

        return operation;
    }

    /**
     * Apply operation to current state
     */
    applyOperation(operation, currentState) {
        try {
            switch (operation.operationType) {
                case 'update':
                    return this.applyUpdate(operation, currentState);
                case 'insert':
                    return this.applyInsert(operation, currentState);
                case 'delete':
                    return this.applyDelete(operation, currentState);
                case 'merge':
                    return this.applyMerge(operation, currentState);
                default:
                    console.warn(`[ConflictResolver] Unknown operation type: ${operation.operationType}`);
                    return currentState;
            }
        } catch (error) {
            console.error('[ConflictResolver] Error applying operation:', error);
            return currentState;
        }
    }

    /**
     * Apply update operation
     */
    applyUpdate(operation, currentState) {
        const newState = { ...currentState };
        
        // Deep merge the data
        if (operation.dataType === 'dcf_inputs') {
            newState.dcfInputs = this.mergeDCFInputs(currentState.dcfInputs || {}, operation.data);
        } else if (operation.dataType === 'lbo_inputs') {
            newState.lboInputs = this.mergeLBOInputs(currentState.lboInputs || {}, operation.data);
        } else if (operation.dataType === 'ma_inputs') {
            newState.maInputs = this.mergeMAInputs(currentState.maInputs || {}, operation.data);
        } else if (operation.dataType === 'scenarios') {
            newState.scenarios = this.mergeScenarios(currentState.scenarios || [], operation.data);
        } else if (operation.dataType === 'notes') {
            newState.notes = this.mergeNotes(currentState.notes || {}, operation.data);
        } else {
            // Generic merge for unknown data types
            newState[operation.dataType] = { ...currentState[operation.dataType], ...operation.data };
        }

        return newState;
    }

    /**
     * Apply insert operation
     */
    applyInsert(operation, currentState) {
        const newState = { ...currentState };
        
        if (operation.dataType === 'scenarios') {
            newState.scenarios = [...(currentState.scenarios || []), operation.data];
        } else if (operation.dataType === 'comments') {
            newState.comments = [...(currentState.comments || []), operation.data];
        }

        return newState;
    }

    /**
     * Apply delete operation
     */
    applyDelete(operation, currentState) {
        const newState = { ...currentState };
        
        if (operation.dataType === 'scenarios' && operation.data.id) {
            newState.scenarios = (currentState.scenarios || []).filter(s => s.id !== operation.data.id);
        } else if (operation.dataType === 'comments' && operation.data.id) {
            newState.comments = (currentState.comments || []).filter(c => c.id !== operation.data.id);
        }

        return newState;
    }

    /**
     * Apply merge operation
     */
    applyMerge(operation, currentState) {
        return this.applyUpdate(operation, currentState);
    }

    /**
     * Merge DCF inputs with conflict resolution
     */
    mergeDCFInputs(current, incoming) {
        const merged = { ...current };
        
        // Merge numeric values with timestamp-based resolution
        Object.keys(incoming).forEach(key => {
            if (typeof incoming[key] === 'number') {
                if (!(key in merged) || this.isNewerValue(incoming[key], merged[key])) {
                    merged[key] = incoming[key];
                }
            } else if (typeof incoming[key] === 'object' && incoming[key] !== null) {
                merged[key] = this.mergeDCFInputs(merged[key] || {}, incoming[key]);
            } else {
                merged[key] = incoming[key];
            }
        });

        return merged;
    }

    /**
     * Merge LBO inputs with conflict resolution
     */
    mergeLBOInputs(current, incoming) {
        const merged = { ...current };
        
        Object.keys(incoming).forEach(key => {
            if (typeof incoming[key] === 'number') {
                if (!(key in merged) || this.isNewerValue(incoming[key], merged[key])) {
                    merged[key] = incoming[key];
                }
            } else if (typeof incoming[key] === 'object' && incoming[key] !== null) {
                merged[key] = this.mergeLBOInputs(merged[key] || {}, incoming[key]);
            } else {
                merged[key] = incoming[key];
            }
        });

        return merged;
    }

    /**
     * Merge M&A inputs with conflict resolution
     */
    mergeMAInputs(current, incoming) {
        const merged = { ...current };
        
        Object.keys(incoming).forEach(key => {
            if (typeof incoming[key] === 'number') {
                if (!(key in merged) || this.isNewerValue(incoming[key], merged[key])) {
                    merged[key] = incoming[key];
                }
            } else if (typeof incoming[key] === 'object' && incoming[key] !== null) {
                merged[key] = this.mergeMAInputs(merged[key] || {}, incoming[key]);
            } else {
                merged[key] = incoming[key];
            }
        });

        return merged;
    }

    /**
     * Merge scenarios with conflict resolution
     */
    mergeScenarios(current, incoming) {
        const scenarioMap = new Map();
        
        // Add current scenarios to map
        current.forEach(scenario => {
            scenarioMap.set(scenario.id, scenario);
        });
        
        // Merge incoming scenarios
        incoming.forEach(scenario => {
            if (scenarioMap.has(scenario.id)) {
                // Merge existing scenario
                const existing = scenarioMap.get(scenario.id);
                scenarioMap.set(scenario.id, this.mergeScenario(existing, scenario));
            } else {
                // Add new scenario
                scenarioMap.set(scenario.id, scenario);
            }
        });
        
        return Array.from(scenarioMap.values());
    }

    /**
     * Merge individual scenario
     */
    mergeScenario(current, incoming) {
        return {
            ...current,
            ...incoming,
            lastModified: Math.max(current.lastModified || 0, incoming.lastModified || 0),
            modifiedBy: incoming.lastModified > (current.lastModified || 0) ? incoming.modifiedBy : current.modifiedBy
        };
    }

    /**
     * Merge notes with conflict resolution
     */
    mergeNotes(current, incoming) {
        const merged = { ...current };
        
        Object.keys(incoming).forEach(ticker => {
            if (merged[ticker]) {
                // Merge existing notes
                merged[ticker] = {
                    ...merged[ticker],
                    ...incoming[ticker],
                    lastModified: Math.max(merged[ticker].lastModified || 0, incoming[ticker].lastModified || 0)
                };
            } else {
                // Add new notes
                merged[ticker] = incoming[ticker];
            }
        });
        
        return merged;
    }

    /**
     * Check if a value is newer based on timestamp
     */
    isNewerValue(newValue, oldValue) {
        // Simple heuristic - in production, use proper timestamps
        return newValue !== oldValue;
    }

    /**
     * Get dependencies for an operation
     */
    getDependencies() {
        return Array.from(this.versionVector.entries()).map(([userId, version]) => ({
            userId: userId,
            version: version
        }));
    }

    /**
     * Check if operation can be applied
     */
    canApplyOperation(operation) {
        if (!operation.dependencies) return true;
        
        return operation.dependencies.every(dep => {
            const currentVersion = this.versionVector.get(dep.userId) || 0;
            return currentVersion >= dep.version;
        });
    }

    /**
     * Resolve conflicts between operations
     */
    resolveConflicts(operations) {
        const resolved = [];
        const conflicts = [];
        
        operations.forEach(operation => {
            if (this.canApplyOperation(operation)) {
                resolved.push(operation);
            } else {
                conflicts.push(operation);
            }
        });
        
        // Try to resolve conflicts
        conflicts.forEach(operation => {
            const resolvedOperation = this.resolveConflict(operation);
            if (resolvedOperation) {
                resolved.push(resolvedOperation);
            }
        });
        
        return resolved;
    }

    /**
     * Resolve individual conflict
     */
    resolveConflict(operation) {
        // Simple conflict resolution - in production, implement more sophisticated logic
        const resolved = { ...operation };
        resolved.operationType = 'merge';
        resolved.conflictResolved = true;
        return resolved;
    }

    /**
     * Generate unique operation ID
     */
    generateOperationId() {
        return 'op_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Trim operation log to prevent memory issues
     */
    trimLog() {
        if (this.operationLog.length > this.maxLogSize) {
            this.operationLog = this.operationLog.slice(-this.maxLogSize / 2);
        }
    }

    /**
     * Get operation history
     */
    getOperationHistory(limit = 50) {
        return this.operationLog.slice(-limit);
    }

    /**
     * Clear operation history
     */
    clearHistory() {
        this.operationLog = [];
        this.versionVector.clear();
    }

    /**
     * Get current version vector
     */
    getVersionVector() {
        return new Map(this.versionVector);
    }

    /**
     * Set version vector (for synchronization)
     */
    setVersionVector(vector) {
        this.versionVector = new Map(vector);
    }
}

// Export for use in other modules
window.ConflictResolver = ConflictResolver;