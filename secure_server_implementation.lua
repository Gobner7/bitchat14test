-- Secure Server Implementation for Shop System
-- This should be in ServerScriptService

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local MarketplaceService = game:GetService("MarketplaceService")

local GameEvent = ReplicatedStorage:WaitForChild("GameEvent")
local GameFunction = ReplicatedStorage:WaitForChild("GameFunction")
local Catalog = ReplicatedStorage:WaitForChild("Catalog")
local Cases = ReplicatedStorage:WaitForChild("Cases")

-- Anti-exploit: Rate limiting
local RateLimit = {}
local RATE_LIMIT_TIME = 0.5 -- 500ms between actions

local function CheckRateLimit(player)
    local now = tick()
    if RateLimit[player] and now - RateLimit[player] < RATE_LIMIT_TIME then
        return false
    end
    RateLimit[player] = now
    return true
end

-- Server-side inventory management
local PlayerInventories = {}

local function GetPlayerInventory(player)
    if not PlayerInventories[player] then
        PlayerInventories[player] = {}
        -- Load from datastore here
    end
    return PlayerInventories[player]
end

local function PlayerOwnsItem(player, itemName)
    local inventory = GetPlayerInventory(player)
    return inventory[itemName] and inventory[itemName] > 0
end

local function AddItemToPlayer(player, itemName, quantity)
    local inventory = GetPlayerInventory(player)
    inventory[itemName] = (inventory[itemName] or 0) + quantity
    
    -- Update client
    -- You would fire a remote event here to update the client's display
    -- RemoteEvents.UpdateInventory:FireClient(player, itemName, inventory[itemName])
end

local function RemoveItemFromPlayer(player, itemName, quantity)
    local inventory = GetPlayerInventory(player)
    if not inventory[itemName] or inventory[itemName] < quantity then
        return false
    end
    inventory[itemName] = inventory[itemName] - quantity
    return true
end

-- Secure purchase validation
local function ValidatePurchase(player, itemName, category)
    local item = Catalog:FindFirstChild(itemName)
    if not item then
        warn("Invalid item:", itemName)
        return false, "Invalid item"
    end
    
    if item.Category.Value ~= category then
        warn("Category mismatch for", player.Name)
        return false, "Category mismatch"
    end
    
    if not item.OnSale.Value then
        return false, "Item not for sale"
    end
    
    if PlayerOwnsItem(player, itemName) then
        return false, "Already owned"
    end
    
    local playerData = player:FindFirstChild("misc")
    if not playerData then
        return false, "Player data not found"
    end
    
    if item.Type.Value == "coins" then
        if playerData.coins.Value < item.Price.Value then
            return false, "Insufficient coins"
        end
        return true, "coins", item.Price.Value
    elseif item.Type.Value == "product" then
        -- Handle Robux purchases differently
        return false, "Use ProcessReceipt for products"
    elseif item.Type.Value == "group" then
        -- Verify group membership
        local groupId = item.GroupId.Value -- Assuming this exists
        if not player:IsInGroup(groupId) then
            return false, "Not in group"
        end
        return true, "group", 0
    elseif item.Type.Value == "premium" then
        if not player.MembershipType == Enum.MembershipType.Premium then
            return false, "Premium required"
        end
        return true, "premium", 0
    end
    
    return false, "Unknown item type"
end

-- Handle purchases
GameEvent.OnServerEvent:Connect(function(player, action, ...)
    -- Rate limiting
    if not CheckRateLimit(player) then
        warn("Rate limit exceeded for", player.Name)
        return
    end
    
    local args = {...}
    
    if action == "purchase" then
        local itemName = args[1]
        local category = args[2]
        
        local success, purchaseType, price = ValidatePurchase(player, itemName, category)
        if not success then
            warn("Purchase validation failed:", purchaseType)
            return
        end
        
        -- Process the purchase
        if purchaseType == "coins" then
            local playerData = player:FindFirstChild("misc")
            playerData.coins.Value = playerData.coins.Value - price
            AddItemToPlayer(player, itemName, 1)
            
            -- Auto-equip
            playerData[category .. "selected"].Value = itemName
            
            print(player.Name, "purchased", itemName, "for", price, "coins")
        end
        
    elseif action == "equip" then
        local itemName = args[1]
        local category = args[2]
        
        if not PlayerOwnsItem(player, itemName) then
            warn(player.Name, "tried to equip unowned item:", itemName)
            return
        end
        
        local playerData = player:FindFirstChild("misc")
        if playerData then
            playerData[category .. "selected"].Value = itemName
        end
        
    elseif action == "unequip" then
        local category = args[1]
        local playerData = player:FindFirstChild("misc")
        if playerData then
            playerData[category .. "selected"].Value = ""
        end
        
    elseif action == "purchasecase" then
        local caseName = args[1]
        local case = Cases:FindFirstChild(caseName)
        
        if not case then
            warn("Invalid case:", caseName)
            return
        end
        
        local playerData = player:FindFirstChild("misc")
        local ownershipValue = playerData[case.OwnershipValue.Value]
        
        if case.Type.Value == "coins" then
            if playerData.coins.Value < case.Price.Value then
                warn(player.Name, "insufficient coins for case")
                return
            end
            
            playerData.coins.Value = playerData.coins.Value - case.Price.Value
            ownershipValue.Value = ownershipValue.Value + 1
            
            print(player.Name, "purchased case:", caseName)
        end
        
    elseif action == "groupcheck" then
        -- Re-validate group items in player's inventory
        -- This is a good practice to periodically check
    end
end)

-- Handle case opening
GameFunction.OnServerInvoke = function(player, action, ...)
    if not CheckRateLimit(player) then
        return nil
    end
    
    local args = {...}
    
    if action == "opencase" then
        local caseName = args[1]
        local case = Cases:FindFirstChild(caseName)
        
        if not case then
            warn("Invalid case:", caseName)
            return nil
        end
        
        local playerData = player:FindFirstChild("misc")
        local ownershipValue = playerData[case.OwnershipValue.Value]
        
        if ownershipValue.Value < 1 then
            warn(player.Name, "tried to open case without ownership")
            return nil
        end
        
        -- Deduct case
        ownershipValue.Value = ownershipValue.Value - 1
        
        -- Generate reward (server-side randomization)
        local reward = GenerateCaseReward(case)
        if reward then
            AddItemToPlayer(player, reward.Name, 1)
            print(player.Name, "got", reward.Name, "from", caseName)
            return reward
        end
        
    elseif action == "redeem" then
        local code = args[1]
        
        -- Validate code server-side
        -- Check if code exists, hasn't been used by player, hasn't expired
        -- This should use a database/datastore
        
        -- Example validation
        if code == "TESTCODE" then
            -- Check if already redeemed
            -- Give reward
            local rewardItem = "Test Sword" -- Example
            AddItemToPlayer(player, rewardItem, 1)
            return rewardItem, "redeemed"
        else
            return nil, "invalid"
        end
    end
    
    return nil
end

-- Generate case rewards server-side
function GenerateCaseReward(case)
    local chances = {}
    local totalWeight = 0
    
    -- Build weighted table
    for _, chance in pairs(case.Chances:GetChildren()) do
        local rarity = tonumber(chance.Name)
        local weight = chance.Value
        totalWeight = totalWeight + weight
        table.insert(chances, {rarity = rarity, weight = weight})
    end
    
    -- Random selection
    local random = math.random() * totalWeight
    local currentWeight = 0
    local selectedRarity = nil
    
    for _, chance in ipairs(chances) do
        currentWeight = currentWeight + chance.weight
        if random <= currentWeight then
            selectedRarity = chance.rarity
            break
        end
    end
    
    -- Get items of selected rarity
    local possibleItems = {}
    for _, itemName in pairs(case.Contents:GetChildren()) do
        local item = Catalog:FindFirstChild(itemName.Name)
        if item and item.Rarity.Value == selectedRarity then
            table.insert(possibleItems, item)
        end
    end
    
    -- Return random item from selected rarity
    if #possibleItems > 0 then
        return possibleItems[math.random(1, #possibleItems)]
    end
    
    return nil
end

-- Handle Robux purchases
MarketplaceService.ProcessReceipt = function(receiptInfo)
    local player = Players:GetPlayerByUserId(receiptInfo.PlayerId)
    if not player then
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end
    
    -- Find the product
    for _, item in pairs(Catalog:GetChildren()) do
        if item.Type.Value == "product" and item.ProductId.Value == receiptInfo.ProductId then
            AddItemToPlayer(player, item.Name, 1)
            return Enum.ProductPurchaseDecision.PurchaseGranted
        end
    end
    
    -- Check for coin products
    local Products = ReplicatedStorage:FindFirstChild("Products")
    if Products then
        for _, product in pairs(Products:GetChildren()) do
            if product.ProductId.Value == receiptInfo.ProductId then
                -- Grant coins
                local coinAmount = product.Coins.Value
                player.misc.coins.Value = player.misc.coins.Value + coinAmount
                return Enum.ProductPurchaseDecision.PurchaseGranted
            end
        end
    end
    
    return Enum.ProductPurchaseDecision.NotProcessedYet
end

-- Clean up on player leaving
Players.PlayerRemoving:Connect(function(player)
    RateLimit[player] = nil
    PlayerInventories[player] = nil
end)