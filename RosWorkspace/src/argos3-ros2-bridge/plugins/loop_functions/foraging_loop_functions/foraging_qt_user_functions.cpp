#include "foraging_qt_user_functions.h"
#include <plugins/bridge/argos_ros_bridge.h>
#include <argos3/core/simulator/entity/controllable_entity.h>

using namespace argos;

/****************************************/
/****************************************/

CForagingQTUserFunctions::CForagingQTUserFunctions() {
   RegisterUserFunction<CForagingQTUserFunctions,CFootBotEntity>(&CForagingQTUserFunctions::Draw);
}

/****************************************/
/****************************************/

void CForagingQTUserFunctions::Draw(CFootBotEntity& c_entity) {
   ArgosRosBridge& cController = dynamic_cast<ArgosRosBridge&>(c_entity.GetControllableEntity().GetController());
   ArgosRosBridge::SFoodData& sFoodData = cController.GetFoodData();
   if(sFoodData.HasFoodItem) {
      DrawCylinder(
         CVector3(0.0f, 0.0f, 0.3f), 
         CQuaternion(),
         0.1f,
         0.05f,
         CColor::BLACK);
   }
   QFont serifFont("Helvetica [Cronyx]", 20, QFont::Bold);
   DrawText(CVector3(0.0, 0.0, 0.5),   // position
            c_entity.GetId().c_str(), // text
            CColor::RED, serifFont); 
}

/****************************************/
/****************************************/

REGISTER_QTOPENGL_USER_FUNCTIONS(CForagingQTUserFunctions, "foraging_qt_user_functions")
