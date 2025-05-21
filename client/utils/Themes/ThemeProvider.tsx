import React, { createContext, useContext, useState, useEffect } from "react";
import { useColorScheme } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { View } from "react-native";

const ThemeContext = createContext<{ appliedTheme: "light" | "dark"; theme: "light" | "dark" | "system"; setTheme: (theme: "light" | "dark" | "system") => void } | undefined>(
    undefined
);

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
    const systemTheme = useColorScheme();
    const [theme, setTheme] = useState<"light" | "dark" | "system">("system");

    useEffect(() => {
        const loadTheme = async () => {
            const savedTheme = await AsyncStorage.getItem("theme");
            if (savedTheme) {
                setTheme(savedTheme as "light" | "dark" | "system");
            }
        };
        loadTheme();
    }, []);

    const setThemeMode = async (selectedTheme: "light" | "dark" | "system") => {
        setTheme(selectedTheme);
        await AsyncStorage.setItem("theme", selectedTheme);
    };

    let appliedTheme = theme === "system" ? (systemTheme ?? "light") : theme;

    // appliedTheme = "light";
    // appliedTheme = "dark";
    
    return (
        <ThemeContext.Provider value={{ appliedTheme,theme, setTheme: setThemeMode }}>
            <View style={{ height: "100%" }} className={appliedTheme}>
                {children}
            </View>
        </ThemeContext.Provider>
    );
};

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error("useTheme must be used within a ThemeProvider");
    }
    return context;
};
