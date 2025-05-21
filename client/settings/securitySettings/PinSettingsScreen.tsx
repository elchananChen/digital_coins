import React from 'react';
import { Box } from '@/components/ui/box';
import { Divider } from '@/components/ui/divider';
import { useTheme } from '@/utils/Themes/ThemeProvider';
import { IC_FaceID_V2, IC_Fingerprint, IC_PIN_V2 } from '@/utils/constants/Icons';
import { Props } from '@/types/NavigationTypes';
import { TouchableOpacity } from 'react-native';
import MyLinearGradient from '@/components/gradient/MyLinearGradient';
import SettingItem from '@/components/SettingItems';
import CardUpRounded from '@/components/CardUpRounded';
import { useTranslation } from 'react-i18next';

const PinSettingsScreen: React.FC<Props> = ({ navigation }) => {
  const { t } = useTranslation();
  const { appliedTheme } = useTheme();

  return (
    <Box className="h-full">
      <MyLinearGradient
        type="background"
        color={appliedTheme === 'light' ? 'purple' : 'blue'}
        className="h-1/4">
        <Box className="h-1/5 justify-end p-4"></Box>
      </MyLinearGradient>
      <CardUpRounded className="p-0">
        <MyLinearGradient type="background" color="light-blue" className="h-full">
          <Box className={`flex gap-2 rounded-t-3xl bg-card-${appliedTheme} w-full p-4`}>
            <TouchableOpacity onPress={() => navigation.navigate('CreatePin')}>
              <SettingItem title={t('pinSettings.createPin')} IconComponent={IC_PIN_V2} />
            </TouchableOpacity>
            <Divider />

            <TouchableOpacity onPress={() => navigation.navigate('FaceId')}>
              <SettingItem title={t('pinSettings.faceId')} IconComponent={IC_FaceID_V2} />
            </TouchableOpacity>
            <Divider />

            <TouchableOpacity onPress={() => navigation.navigate('TouchId')}>
              <SettingItem title={t('pinSettings.touchId')} IconComponent={IC_Fingerprint} />
            </TouchableOpacity>
            <Divider />
          </Box>
        </MyLinearGradient>
      </CardUpRounded>
    </Box>
  );
};

export default PinSettingsScreen;
