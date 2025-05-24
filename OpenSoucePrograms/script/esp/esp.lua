-- LocalScript (recommended)
-- Place this under StarterPlayer > StarterPlayerScripts

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage") -- For potential debug messages to server
local ServerStorage = game:GetService("ServerStorage") -- For potential debug messages to server (if script is server-sided)

-- Create a table to store highlighted player data (Highlight instance, NameTag BillboardGui)
local highlightedPlayers = {} 

-- Function to create and configure the name tag BillboardGui
local function createNameTag(character, name)
    -- Check if a name tag already exists to prevent duplication
    if character:FindFirstChild("NameTagBillboard") then
        warn("DEBUG: NameTagBillboard already exists for character:", character.Name)
        return character:FindFirstChild("NameTagBillboard")
    end

    local billboardGui = Instance.new("BillboardGui")
    billboardGui.Name = "NameTagBillboard"
    billboardGui.Size = UDim2.new(3, 0, 1, 0) -- Size of the BillboardGui (relative to screen space and pixels)
    billboardGui.StudsOffset = Vector3.new(0, 2, 0) -- Offset upwards to display name above the character's head
    billboardGui.AlwaysOnTop = true -- Ensures it's always displayed on top of other 3D objects (for "wallhack" effect)
    billboardGui.ExtentsOffset = Vector3.new(0, 0, 0) -- Prevents clipping with the character model
    
    warn("DEBUG: Created BillboardGui for", name)

    local textLabel = Instance.new("TextLabel")
    textLabel.Name = "NameLabel"
    textLabel.Size = UDim2.new(1, 0, 1, 0) -- Fill the entire BillboardGui
    textLabel.BackgroundTransparency = 1 -- Make the background transparent
    textLabel.Text = name
    textLabel.TextColor3 = Color3.fromRGB(255, 255, 255) -- White text color
    textLabel.Font = Enum.Font.SourceSansBold -- Bold font
    textLabel.TextScaled = true -- Automatically scale text to fit
    textLabel.TextStrokeTransparency = 0.5 -- Text stroke transparency
    textLabel.TextStrokeColor3 = Color3.fromRGB(0, 0, 0) -- Black text stroke color
    textLabel.Parent = billboardGui

    billboardGui.Parent = character -- Attach the BillboardGui to the character model
    warn("DEBUG: Attached NameTag to character:", character.Name)
    return billboardGui
end

-- Function to apply highlight and name tag to a player
local function highlightPlayer(player)
    if not highlightedPlayers[player.UserId] then
        local character = player.Character or player.CharacterAdded:Wait() -- Get character or wait for it to load

        if character then
            warn("DEBUG: Highlighting player:", player.Name, "with character:", character.Name)
            -- Create Highlight instance
            local highlight = Instance.new("Highlight")
            highlight.Parent = character
            highlight.FillColor = Color3.fromRGB(255, 255, 0) -- Fill color (Yellow)
            highlight.OutlineColor = Color3.fromRGB(255, 0, 0) -- Outline color (Red)
            highlight.FillTransparency = 0.5 -- Fill transparency
            highlight.OutlineTransparency = 0 -- Outline transparency
            warn("DEBUG: Created Highlight for", player.Name)

            -- Create and display name tag
            local nameTag = createNameTag(character, player.Name)

            -- Store both instances in the tracking table
            highlightedPlayers[player.UserId] = {
                Highlight = highlight,
                NameTag = nameTag
            }
            warn("DEBUG: Stored highlight data for player:", player.Name)
        else
            warn("DEBUG: Failed to get character for player:", player.Name)
        end
    else
        warn("DEBUG: Player", player.Name, "is already highlighted. Skipping.")
    end
end

-- Function to remove highlight and name tag from a player
local function removeHighlight(player)
    if highlightedPlayers[player.UserId] then
        warn("DEBUG: Removing highlight and name tag for player:", player.Name)
        if highlightedPlayers[player.UserId].Highlight then
            highlightedPlayers[player.UserId].Highlight:Destroy()
            warn("DEBUG: Destroyed Highlight for", player.Name)
        end
        if highlightedPlayers[player.UserId].NameTag then
            highlightedPlayers[player.UserId].NameTag:Destroy()
            warn("DEBUG: Destroyed NameTag for", player.Name)
        end
        highlightedPlayers[player.UserId] = nil -- Clear entry from tracking table
        warn("DEBUG: Cleared highlight data for player:", player.Name)
    else
        warn("DEBUG: No highlight data found for player:", player.Name, "to remove.")
    end
end

-- --- Initial setup ---

-- Highlight all players currently in the game when the script starts
warn("DEBUG: Script started. Highlighting existing players.")
for _, player in ipairs(Players:GetPlayers()) do
    highlightPlayer(player)
end

-- --- Event Listeners ---

-- Listen for new players joining the game
Players.PlayerAdded:Connect(function(player)
    warn("DEBUG: PlayerAdded event triggered for:", player.Name)
    -- Listen for the player's character to be added/loaded
    player.CharacterAdded:Connect(function(character)
        warn("DEBUG: CharacterAdded event triggered for:", player.Name, "character:", character.Name)
        -- Wait a short moment to ensure character model is fully loaded
        task.wait(0.1) 
        highlightPlayer(player)
    end)
end)

-- Listen for players leaving the game
Players.PlayerRemoving:Connect(function(player)
    warn("DEBUG: PlayerRemoving event triggered for:", player.Name)
    removeHighlight(player)
end)

-- --- Continuous Update Loop ---

-- Use Heartbeat for continuous updates to ensure highlight and name tag persistence
-- This is crucial for handling character reloads (e.g., after dying)
RunService.Heartbeat:Connect(function()
    for _, player in ipairs(Players:GetPlayers()) do
        local highlightData = highlightedPlayers[player.UserId]
        local character = player.Character

        if character then
            -- If character exists but no highlight data is stored, create it
            if not highlightData then 
                warn("DEBUG: Heartbeat: Found character for", player.Name, "but no highlight data. Re-highlighting.")
                highlightPlayer(player)
            else
                -- Ensure Highlight is parented to the current character
                if highlightData.Highlight and highlightData.Highlight.Parent ~= character then
                    warn("DEBUG: Heartbeat: Re-parenting Highlight for", player.Name, "to new character.")
                    highlightData.Highlight.Parent = character
                elseif not highlightData.Highlight then -- If Highlight instance is missing
                    warn("DEBUG: Heartbeat: Highlight instance missing for", player.Name, ". Recreating.")
                    highlightData.Highlight = Instance.new("Highlight")
                    highlightData.Highlight.Parent = character
                    highlightData.Highlight.FillColor = Color3.fromRGB(255, 255, 0)
                    highlightData.Highlight.OutlineColor = Color3.fromRGB(255, 0, 0)
                    highlightData.Highlight.FillTransparency = 0.5
                    highlightData.Highlight.OutlineTransparency = 0
                end

                -- Ensure NameTag is parented to the current character
                if highlightData.NameTag and highlightData.NameTag.Parent ~= character then
                    warn("DEBUG: Heartbeat: Re-parenting NameTag for", player.Name, "to new character.")
                    highlightData.NameTag.Parent = character
                elseif not highlightData.NameTag then -- If NameTag instance is missing
                    warn("DEBUG: Heartbeat: NameTag instance missing for", player.Name, ". Recreating.")
                    highlightData.NameTag = createNameTag(character, player.Name)
                end
            end
        elseif highlightData then -- If character does not exist but highlight data is present, remove it
            warn("DEBUG: Heartbeat: Character for", player.Name, "is nil but highlight data exists. Removing.")
            removeHighlight(player)
        end
    end
end)

warn("DEBUG: Script initialized.")