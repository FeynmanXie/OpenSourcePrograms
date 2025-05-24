-- Script (Server-Side - For infinite health)
-- Place this under Workspace or ServerScriptService

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local HEAL_INTERVAL = 1 -- How often to heal (in seconds)
local DEBUG_MODE = true -- Set to true to see debug messages in the server output

-- Function to heal a player
local function healPlayer(player)
    local character = player.Character
    if character then
        local humanoid = character:FindFirstChildOfClass("Humanoid")
        if humanoid and humanoid.Health < humanoid.MaxHealth then
            humanoid.Health = humanoid.MaxHealth -- Set health to max
            if DEBUG_MODE then
                warn("DEBUG (Server): Healed", player.Name, "to full health.")
            end
        elseif DEBUG_MODE and not humanoid then
            warn("DEBUG (Server): No Humanoid found for", player.Name, "'s character.")
        end
    elseif DEBUG_MODE then
        warn("DEBUG (Server): No character found for player:", player.Name)
    end
end

-- Function to set up continuous healing for a player
local function setupPlayerHealing(player)
    -- Disconnect any previous connections to avoid duplicates
    if player:GetAttribute("HealingConnection") then
        local connection = player:GetAttribute("HealingConnection")
        if connection and typeof(connection) == "RBXScriptConnection" and connection.Connected then
            connection:Disconnect()
            if DEBUG_MODE then
                warn("DEBUG (Server): Disconnected old healing connection for", player.Name)
            end
        end
        player:SetAttribute("HealingConnection", nil)
    end

    -- Create a loop to heal the player every HEAL_INTERVAL seconds
    local connection = RunService.Heartbeat:Connect(function()
        healPlayer(player)
    end)
    
    -- Store the connection so we can disconnect it if the player leaves
    player:SetAttribute("HealingConnection", connection)
    if DEBUG_MODE then
        warn("DEBUG (Server): Setup continuous healing for player:", player.Name)
    end
end

-- Function to stop healing for a player
local function stopPlayerHealing(player)
    if player:GetAttribute("HealingConnection") then
        local connection = player:GetAttribute("HealingConnection")
        if connection and typeof(connection) == "RBXScriptConnection" and connection.Connected then
            connection:Disconnect()
            if DEBUG_MODE then
                warn("DEBUG (Server): Stopped healing for player:", player.Name)
            end
        end
        player:SetAttribute("HealingConnection", nil)
    end
end

-- --- Initial setup ---

-- Set up healing for all players currently in the game when the script starts
if DEBUG_MODE then
    warn("DEBUG (Server): Script started. Setting up healing for existing players.")
end
for _, player in ipairs(Players:GetPlayers()) do
    setupPlayerHealing(player)
end

-- --- Event Listeners ---

-- Listen for new players joining
Players.PlayerAdded:Connect(function(player)
    if DEBUG_MODE then
        warn("DEBUG (Server): PlayerAdded event triggered for:", player.Name)
    end
    -- It's crucial to wait for the character to be added before attempting to heal
    player.CharacterAdded:Connect(function(character)
        if DEBUG_MODE then
            warn("DEBUG (Server): CharacterAdded event triggered for:", player.Name, "character:", character.Name)
        end
        -- Give a small delay to ensure Humanoid is fully initialized
        task.wait(0.1) 
        setupPlayerHealing(player)
    end)
end)

-- Listen for players leaving to clean up connections
Players.PlayerRemoving:Connect(function(player)
    if DEBUG_MODE then
        warn("DEBUG (Server): PlayerRemoving event triggered for:", player.Name)
    end
    stopPlayerHealing(player)
end)

if DEBUG_MODE then
    warn("DEBUG (Server): Infinite health script initialized.")
end