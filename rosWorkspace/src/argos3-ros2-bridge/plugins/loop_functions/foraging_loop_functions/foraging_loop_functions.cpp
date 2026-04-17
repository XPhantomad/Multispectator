#include "foraging_loop_functions.h"
#include <argos3/core/simulator/simulator.h>
#include <argos3/core/utility/configuration/argos_configuration.h>
#include <argos3/plugins/robots/foot-bot/simulator/footbot_entity.h>
#include <plugins/bridge/argos_ros_bridge.h>

/****************************************/
/****************************************/

CForagingLoopFunctions::CForagingLoopFunctions() :
   m_cForagingArenaSideX(-0.9f, 1.7f),
   m_cForagingArenaSideY(-1.7f, 1.7f),
   m_pcFloor(NULL),
   m_pcRNG(NULL),
   m_unCollectedFood(0),
   m_nEnergy(0),
   m_unEnergyPerFoodItem(1),
   m_unEnergyPerWalkingRobot(1) {
}

/****************************************/
/****************************************/

void CForagingLoopFunctions::Init(TConfigurationNode& t_node) {
   try {
      TConfigurationNode& tForaging = GetNode(t_node, "foraging");
      /* Get a pointer to the floor entity */
      m_pcFloor = &GetSpace().GetFloorEntity();
      /* Get the number of food items we want to be scattered from XML */
      UInt32 unFoodItems;
      GetNodeAttribute(tForaging, "items", unFoodItems);
      /* Get the number of food items we want to be scattered from XML */
      GetNodeAttribute(tForaging, "radius", m_fFoodSquareRadius);
      m_fFoodSquareRadius *= m_fFoodSquareRadius;
      
      /* Get prey position */
      float xPos, yPos;	
      GetNodeAttribute(tForaging, "xpos", xPos);
      GetNodeAttribute(tForaging, "ypos", yPos);

      /* Create a new RNG */
      m_pcRNG = CRandom::CreateRNG("argos");
      /* Distribute uniformly the items in the environment */
      for(UInt32 i = 0; i < unFoodItems; ++i) {
         m_cFoodPos.push_back(CVector2(xPos, yPos));
      }
   }
   catch(CARGoSException& ex) {
      THROW_ARGOSEXCEPTION_NESTED("Error parsing loop functions!", ex);
   }
}

/****************************************/
/****************************************/

void CForagingLoopFunctions::Reset() {
   /* Zero the counters */
   m_unCollectedFood = 0;
   m_nEnergy = 0;
   /* Close the file */
   m_cOutput.close();
   /* Open the file, erasing its contents */
   m_cOutput.open(m_strOutput.c_str(), std::ios_base::trunc | std::ios_base::out);
   m_cOutput << "# clock\twalking\tresting\tcollected_food\tenergy" << std::endl;
   /* Distribute uniformly the items in the environment */
   for(UInt32 i = 0; i < m_cFoodPos.size(); ++i) {
      m_cFoodPos[i].Set(m_preyPosition.GetX(), m_preyPosition.GetY());
   }
}

/****************************************/
/****************************************/

void CForagingLoopFunctions::Destroy() {
   /* Close the file */
   m_cOutput.close();
}

/****************************************/
/****************************************/

CColor CForagingLoopFunctions::GetFloorColor(const CVector2& c_position_on_plane) {
   for(UInt32 i = 0; i < m_cFoodPos.size(); ++i) {
      if((c_position_on_plane - m_cFoodPos[i]).SquareLength() < m_fFoodSquareRadius) {
         return CColor::BLACK;
      }
   }
   // 
   Real spacing = 0.25;
   Real thickness = 0.005;

     auto mod = [](Real value, Real spacing) {
       return fmod(fmod(value, spacing) + spacing, spacing);
   };

   Real x_mod = mod(c_position_on_plane.GetX(), spacing);
   Real y_mod = mod(c_position_on_plane.GetY(), spacing);

   if (x_mod < thickness || y_mod < thickness) {
       return CColor::GRAY50;  // Gridlinie
   }


   return CColor::WHITE;  // Bodenfarbe dazwischen


}

/****************************************/
/****************************************/

void CForagingLoopFunctions::PreStep() {
   /* Logic to pick and drop food items */
   /*
    * If a robot is in the nest, drop the food item
    * If a robot is on a food item, pick it
    * Each robot can carry only one food item per time
    */
   UInt32 unWalkingFBs = 0;
   UInt32 unRestingFBs = 0;
   /* Check whether a robot is on a food item */
   CSpace::TMapPerType& m_cFootbots = GetSpace().GetEntitiesByType("foot-bot");

   for(CSpace::TMapPerType::iterator it = m_cFootbots.begin();
       it != m_cFootbots.end();
       ++it) {
      /* Get handle to foot-bot entity and controller */
      CFootBotEntity& cFootBot = *any_cast<CFootBotEntity*>(it->second);
      ArgosRosBridge& cController = dynamic_cast<ArgosRosBridge&>(cFootBot.GetControllableEntity().GetController());
      /* Count how many foot-bots are in which state */
      if(! cController.IsResting()) ++unWalkingFBs;
      else ++unRestingFBs;
      /* Get the position of the foot-bot on the ground as a CVector2 */
      CVector2 cPos;
      cPos.Set(cFootBot.GetEmbodiedEntity().GetOriginAnchor().Position.GetX(),
               cFootBot.GetEmbodiedEntity().GetOriginAnchor().Position.GetY());
      /* Get food data */
      ArgosRosBridge::SFoodData& sFoodData = cController.GetFoodData();
      /* The foot-bot has a food item and Unload is triggered*/
      if(sFoodData.HasFoodItem) {
         /* Otherwise place the food item under the robot on the ground so that joiner can load it" */
         if (sFoodData.Unload) {
            /* Place food item on the ground */
            if (cPos.GetX() <= -2.5) {
              m_cFoodPos[sFoodData.FoodItemIdx].Set(m_preyPosition.GetX(), m_preyPosition.GetY());
            }
            else {
              m_cFoodPos[sFoodData.FoodItemIdx].Set(cPos.GetX(),
                                                  cPos.GetY());
            }
            /* Drop the food item */
            sFoodData.HasFoodItem = false;
            sFoodData.FoodItemIdx = 0;
            ++sFoodData.TotalFoodItems;
            /* The floor texture must be updated */
            m_pcFloor->SetChanged();
         }
      }
      else {
         /* The foot-bot has no food item */
         /* Check whether the foot-bot is out of the nest */
          bool bDone = false;
          for(size_t i = 0; i < m_cFoodPos.size() && !bDone; ++i) {
             if((cPos - m_cFoodPos[i]).SquareLength() < m_fFoodSquareRadius && sFoodData.Load) {
                /* If so, we move that item out of sight */
                m_cFoodPos[i].Set(100.0f, 100.0f);
                /* The foot-bot is now carrying an item */
                sFoodData.HasFoodItem = true;
                sFoodData.FoodItemIdx = i;
                /* The floor texture must be updated */
                m_pcFloor->SetChanged();
                /* We are done */
                bDone = true;
             }
          }
      }
   }
}

/****************************************/
/****************************************/

REGISTER_LOOP_FUNCTIONS(CForagingLoopFunctions, "foraging_loop_functions")
