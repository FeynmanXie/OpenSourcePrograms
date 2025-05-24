-- LocalScript (The "Hard Challenge" - Client-side flight/no-clip)
-- Place this under StarterPlayer > StarterPlayerScripts

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local PhysicsService = game:GetService("PhysicsService")

local localPlayer = Players.LocalPlayer
local flying = false
local flySpeed = 50 -- Adjust flight speed as needed
local initialGravity = workspace.Gravity -- Store initial gravity

-- Collision group for no-clip
local NO_CLIP_GROUP_NAME = "NoClipGroup"
local NO_COLLIDE_GROUP_NAME = "Default" -- We want to make NoClipGroup not collide with Default

-- Setup collision groups (run once)
local function setupCollisionGroups()
    local success, err = pcall(function()
        local groupExists = false
        for i = 0, 31 do
            local name = PhysicsService:GetCollisionGroupName(i)
            if name == NO_CLIP_GROUP_NAME then
                groupExists = true
                break
            end
        end

        if not groupExists then
            local newGroup = PhysicsService:CreateCollisionGroup(NO_CLIP_GROUP_NAME)
            warn("DEBUG: Created collision group:", NO_CLIP_GROUP_NAME)
        end

        -- Ensure NoClipGroup does not collide with Default group
        if not PhysicsService:CollisionGroupsAreCollidable(NO_CLIP_GROUP_NAME, NO_COLLIDE_GROUP_NAME) then
            PhysicsService:SetCollisionGroupCollidable(NO_CLIP_GROUP_NAME, NO_COLLIDE_GROUP_NAME, false)
            warn("DEBUG: Set collision for", NO_CLIP_GROUP_NAME, "and", NO_COLLIDE_GROUP_NAME, "to false.")
        end
    end)
    if not success then
        warn("DEBUG: Failed to setup collision groups:", err)
    end
end

setupCollisionGroups() -- Call once when script starts

-- Function to toggle flight mode
local function toggleFlight()
    local character = localPlayer.Character
    if not character then return end

    flying = not flying
    warn("DEBUG: Flight Toggled:", flying)

    if flying then
        -- Disable player movement controls (optional, but good for dedicated flight)
        localPlayer.DevComputerMovementMode = Enum.DevComputerMovementMode.Scriptable
        localPlayer.DevTouchMovementMode = Enum.DevTouchMovementMode.Scriptable

        -- Disable gravity for the character's HumanoidRootPart
        -- Note: Direct gravity modification on HumanoidRootPart's body force is usually not needed if position is set
        -- But setting workspace gravity to 0 is common for "god mode" flight.
        workspace.Gravity = 0
        warn("DEBUG: Gravity set to 0.")

        -- Set parts to the no-clip collision group
        for _, part in ipairs(character:GetDescendants()) do
            if part:IsA("BasePart") then
                PhysicsService:SetPartCollisionGroup(part, NO_CLIP_GROUP_NAME)
            end
        end
        warn("DEBUG: Character parts set to NoClipGroup.")

        -- Store current CFrame to maintain position when starting flight
        local currentCFrame = character.HumanoidRootPart.CFrame
        RunService.Heartbeat:Connect(function()
            if flying and character and character.HumanoidRootPart then
                -- Constantly update the HumanoidRootPart's CFrame to bypass physics
                character.HumanoidRootPart.CFrame = currentCFrame 
            end
        end)

    else
        -- Re-enable player movement controls
        localPlayer.DevComputerMovementMode = Enum.DevComputerMovementMode.UserChoice
        localPlayer.DevTouchMovementMode = Enum.DevTouchMovementMode.UserChoice

        -- Restore original gravity
        workspace.Gravity = initialGravity
        warn("DEBUG: Gravity restored to:", initialGravity)

        -- Reset parts to default collision group
        for _, part in ipairs(character:GetDescendants()) do
            if part:IsA("BasePart") then
                PhysicsService:SetPartCollisionGroup(part, NO_COLLIDE_GROUP_NAME)
            end
        end
        warn("DEBUG: Character parts reset to Default collision group.")
    end
end

-- Listen for key presses (e.g., "F" key to toggle flight)
UserInputService.InputBegan:Connect(function(input, gameProcessedEvent)
    if gameProcessedEvent then return end -- Ignore if game UI consumed the input

    if input.KeyCode == Enum.KeyCode.F then -- 'F' key to toggle flight
        toggleFlight()
    end
end)

-- Flight movement loop
RunService.Heartbeat:Connect(function(dt)
    if flying and localPlayer.Character and localPlayer.Character.HumanoidRootPart then
        local humanoidRootPart = localPlayer.Character.HumanoidRootPart
        local moveDirection = Vector3.new(0, 0, 0)
        
        -- Get player input for movement (W, A, S, D for horizontal, Space for up, LeftShift for down)
        if UserInputService:IsKeyDown(Enum.KeyCode.W) then
            moveDirection = moveDirection + humanoidRootPart.CFrame.lookVector
        end
        if UserInputService:IsKeyDown(Enum.KeyCode.S) then
            moveDirection = moveDirection - humanoidRootPart.CFrame.lookVector
        end
        if UserInputService:IsKeyDown(Enum.KeyCode.A) then
            moveDirection = moveDirection - humanoidRootPart.CFrame.rightVector
        end
        if UserInputService:IsKeyDown(Enum.KeyCode.D) then
            moveDirection = moveDirection + humanoidRootPart.CFrame.rightVector
        end
        if UserInputService:IsKeyDown(Enum.KeyCode.Space) then
            moveDirection = moveDirection + Vector3.new(0, 1, 0) -- Up
        end
        if UserInputService:IsKeyDown(Enum.KeyCode.LeftShift) then
            moveDirection = moveDirection - Vector3.new(0, 1, 0) -- Down
        end

        -- Normalize direction to prevent faster diagonal movement
        if moveDirection.Magnitude > 0 then
            moveDirection = moveDirection.Unit
        end

        -- Apply movement
        humanoidRootPart.CFrame = humanoidRootPart.CFrame + moveDirection * flySpeed * dt
    end
end)

warn("DEBUG: Flight script initialized. Press 'F' to toggle flight.")