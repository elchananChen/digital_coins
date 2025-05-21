import React from "react";
import { Text } from "react-native";
import { Box } from "@/components/ui/box";
import { Icon } from "@/components/ui/icon";
import { ChevronRight } from "lucide-react-native";
import { IC_ChevronRight, IC_ChevronRight_White } from "@/utils/constants/Icons";
import { useTheme } from "@/utils/Themes/ThemeProvider";

interface SettingItemProps {
    title: string;
    IconComponent?: React.ElementType;
    badge?: string;
}

const SettingItem: React.FC<SettingItemProps> = ({ title, IconComponent, badge }) => {
    const { appliedTheme } = useTheme();
    return (
        <Box className="flex flex-row items-center">
            <Box className="flex-row items-center gap-3 flex-1">
                <Box className="rounded-full p-2">
                    {IconComponent && <IconComponent className="w-12 h-12" />}
                </Box>
                <Text className={`text-text-${appliedTheme} font-medium text-[17px]`}>{title}</Text>
            </Box>
            <Box className="ml-auto">
                <Box className="flex flex-row justify-center items-center gap-1 ">
                    {badge && (
                        <Box className={`bg-badge-${appliedTheme} p-1 rounded-full`}>
                            <Text className="text-purple-500 ml-1 mr-1 text-[13px]">
                                {badge}
                            </Text>
                        </Box>
                    )}
                    {appliedTheme === 'dark' ? (
                        <IC_ChevronRight_White className="w-4 h-4" />
                    ) : (
                        <IC_ChevronRight className="w-4 h-4" />
                    )}
                </Box>
            </Box>
        </Box>
    );
};

export default SettingItem;
